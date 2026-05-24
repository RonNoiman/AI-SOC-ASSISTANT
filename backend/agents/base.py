import logging
import re

from data.threat_catalog import VALID_THREAT_IDS, classify_query as classify_threat

logger = logging.getLogger("soc.agent")

MODEL = "llama-3.3-70b-versatile"

# SOC-standard severity ladder, highest to lowest.
VALID_SEVERITIES = ("Critical", "High", "Medium", "Low", "Informational")
DEFAULT_SEVERITY = "Medium"

VALID_STRIDE = (
    "Spoofing",
    "Tampering",
    "Repudiation",
    "Information Disclosure",
    "Denial of Service",
    "Elevation of Privilege",
)

# Appended to every agent's system prompt so all three specialists return the
# same triage shape: a parseable transparency header followed by structured
# Markdown. Order is fixed so the parser stays simple.
STRUCTURED_OUTPUT_INSTRUCTION = """
Always begin your answer with a 7-line transparency header in exactly this order,
each on its own line, and then a blank line, and then the Markdown sections.

SEVERITY: <one of: Critical | High | Medium | Low | Informational>
CONFIDENCE: <decimal between 0.00 and 1.00 - how confident you are in this triage>
THREAT_ID: <one of: T1 | T2 | T3 | T4 | T5 | T6 | T7 | T8 | NONE>
STRIDE: <one of: Spoofing | Tampering | Repudiation | Information Disclosure | Denial of Service | Elevation of Privilege>
INDICATORS: <comma-separated concrete indicators you matched in the input>
REASONING: <one sentence: why this severity / threat / STRIDE category>
ACTION: <one short sentence: the single most important next step for the analyst>

Then the Markdown body, in this exact order:

### Summary
One or two plain-language sentences describing what is happening.

### Indicators of Compromise (IOCs)
Bullet list of concrete IOCs in the event - IP addresses, domains, file hashes,
usernames, ports. Write "None identified" if none are present.

### MITRE ATT&CK Mapping
The most relevant ATT&CK technique(s) as `Txxxx - Name`, or "Not determined".

### Recommended Actions
A numbered list of concrete defensive next steps for the analyst.

### Escalation Path
Who to notify and when (SOC lead, incident response team, asset owner, etc).

Threat catalog reference:
- T1 Prompt Injection / Jailbreak (Tampering)
- T2 Credential Stuffing / Brute Force (Spoofing)
- T3 Reconnaissance / Port Scanning (Information Disclosure)
- T4 Privilege Escalation Attempt (Elevation of Privilege)
- T5 Insider Threat / Anomalous Access (Information Disclosure)
- T6 Data Exfiltration (Information Disclosure)
- T7 Policy Violation / Compliance Gap (Repudiation)
- T8 Malware / Suspicious Process (Tampering)

Rules:
- Choose severity from the analyst's point of view: business impact x likelihood.
- Stay strictly defensive. Never produce offensive tradecraft, exploit code,
  or attacker steps.
- If no threat-catalog entry fits, set THREAT_ID to NONE - do not invent one.
""".strip()


# ─── Transparency parser ──────────────────────────────────────────────────────
# The LLM is asked to emit a 7-line header before the Markdown body. We parse
# each known key from the first ~20 lines, then strip those lines from the body
# so the UI renders only the prose. The parser is forgiving: any missing field
# falls back to a deterministic default so we never crash on a malformed reply.

_HEADER_KEYS = ("SEVERITY", "CONFIDENCE", "THREAT_ID", "STRIDE", "INDICATORS", "REASONING", "ACTION")
_HEADER_LINE = re.compile(
    rf"^\s*({'|'.join(_HEADER_KEYS)})\s*:\s*(.*?)\s*$",
    re.IGNORECASE,
)


def _normalize_severity(raw: str) -> str:
    if not raw:
        return DEFAULT_SEVERITY
    candidate = raw.strip().capitalize()
    return candidate if candidate in VALID_SEVERITIES else DEFAULT_SEVERITY


def _normalize_confidence(raw: str) -> float:
    if not raw:
        return 0.5
    try:
        value = float(raw.strip().rstrip("%"))
    except ValueError:
        return 0.5
    if value > 1.0:  # The model sometimes emits 0..100.
        value /= 100.0
    return max(0.0, min(1.0, value))


def _normalize_threat_id(raw: str) -> str | None:
    if not raw:
        return None
    candidate = raw.strip().upper()
    if candidate in {"NONE", "N/A", "-", ""}:
        return None
    return candidate if candidate in VALID_THREAT_IDS else None


def _normalize_stride(raw: str) -> str | None:
    if not raw:
        return None
    target = raw.strip().lower()
    for category in VALID_STRIDE:
        if category.lower() == target:
            return category
    return None


def _normalize_indicators(raw: str) -> list[str]:
    if not raw:
        return []
    parts = [p.strip(" -•*\t") for p in re.split(r"[,;]", raw)]
    return [p for p in parts if p]


def extract_transparency(text: str, *, query: str = "") -> tuple[dict, str]:
    """Parse the transparency header and return (transparency_dict, body).

    The body is the markdown content with the header stripped. Missing fields
    fall back to safe defaults so the API contract is always well-formed.
    Threat-id falls back to a keyword classifier against the query.
    """
    parsed: dict[str, str] = {}
    body_start = 0
    header_active = True

    lines = text.splitlines()
    for idx, line in enumerate(lines[:20]):  # only scan the prelude
        if not line.strip():
            if parsed:  # blank line after a real header ends the prelude
                body_start = idx + 1
                break
            continue
        m = _HEADER_LINE.match(line)
        if m:
            key = m.group(1).upper()
            if key not in parsed:
                parsed[key] = m.group(2)
            body_start = idx + 1
        else:
            if header_active and parsed:
                # Hit prose - the header ends here.
                body_start = idx
                break
            if not parsed:
                # No header at all; leave body untouched.
                body_start = 0
                break

    body = "\n".join(lines[body_start:]).lstrip() if parsed else text

    severity = _normalize_severity(parsed.get("SEVERITY", ""))
    confidence = _normalize_confidence(parsed.get("CONFIDENCE", ""))
    threat_id = _normalize_threat_id(parsed.get("THREAT_ID", ""))
    stride = _normalize_stride(parsed.get("STRIDE", ""))
    indicators = _normalize_indicators(parsed.get("INDICATORS", ""))
    reasoning = (parsed.get("REASONING", "") or "").strip()
    action = (parsed.get("ACTION", "") or "").strip()

    # Deterministic backstop when the LLM omitted the threat id.
    if threat_id is None and query:
        threat_id = classify_threat(query)

    transparency = {
        "severity": severity,
        "confidence_score": round(confidence, 2),
        "threat_id": threat_id,
        "stride_category": stride,
        "matched_indicators": indicators,
        "reasoning": reasoning,
        "recommended_action": action,
    }
    return transparency, body


def extract_severity(text: str) -> tuple[str, str]:
    """Back-compat wrapper around extract_transparency for older callers/tests."""
    transparency, body = extract_transparency(text)
    return transparency["severity"], body


class BaseAgent:
    """Shared behaviour for the three SOC specialist agents.

    Subclasses only declare their domain-specific prompt content and demo-mode
    playbook; the LLM call, structured-output contract, and transparency parsing
    all live here so the three agents stay consistent.
    """

    domain_name = "Security"
    specialties = ""          # Markdown bullet block listing the agent's focus areas.
    refusal_clause = (
        "Refuse to produce offensive instructions, exploit code, or attacker tradecraft."
    )

    # Demo-mode (no GROQ_API_KEY) playbook.
    demo_summary = ""
    demo_actions: list[str] = []
    demo_escalation = ""
    demo_severity = DEFAULT_SEVERITY
    demo_threat_id: str | None = None
    demo_stride: str | None = None
    demo_confidence = 0.55
    demo_indicators: list[str] = []
    demo_reasoning = ""
    demo_recommended_action = ""

    def __init__(self, client):
        self.client = client

    @property
    def system_prompt(self) -> str:
        return (
            f"You are a {self.domain_name} Agent in a SOC (Security Operations Center).\n"
            f"You specialize in:\n{self.specialties}\n\n"
            "Provide clear, defensive, actionable answers. Always apply the principle "
            f"of least privilege and zero-trust thinking. {self.refusal_clause}\n\n"
            f"{STRUCTURED_OUTPUT_INSTRUCTION}"
        )

    def _demo_body(self) -> str:
        actions = "\n".join(f"{i}. {a}" for i, a in enumerate(self.demo_actions, 1))
        return (
            f"### Summary\n{self.demo_summary}\n\n"
            "### Indicators of Compromise (IOCs)\n"
            "None identified - running in demo mode without an LLM.\n\n"
            "### MITRE ATT&CK Mapping\nNot determined (demo mode).\n\n"
            f"### Recommended Actions\n{actions}\n\n"
            f"### Escalation Path\n{self.demo_escalation}\n\n"
            "_Demo mode: set GROQ_API_KEY in backend/.env for full LLM-driven analysis._"
        )

    def _demo_transparency(self, query: str) -> dict:
        return {
            "severity": self.demo_severity,
            "confidence_score": self.demo_confidence,
            "threat_id": self.demo_threat_id or classify_threat(query),
            "stride_category": self.demo_stride,
            "matched_indicators": list(self.demo_indicators),
            "reasoning": self.demo_reasoning,
            "recommended_action": self.demo_recommended_action,
        }

    async def run(self, query: str, history: list[dict]) -> dict:
        """Return ``{"response": markdown, "severity": level, "transparency": {...}}``."""
        if self.client is None:
            transparency = self._demo_transparency(query)
            return {
                "response": self._demo_body(),
                "severity": transparency["severity"],
                "transparency": transparency,
            }

        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": query})

        try:
            completion = self.client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=0.3,
                max_tokens=2048,
            )
            raw = completion.choices[0].message.content or ""
        except Exception as exc:
            logger.warning(
                "%s LLM call failed, falling back to demo response: %s",
                self.domain_name, exc,
            )
            transparency = self._demo_transparency(query)
            return {
                "response": self._demo_body(),
                "severity": transparency["severity"],
                "transparency": transparency,
            }

        transparency, body = extract_transparency(raw, query=query)
        return {
            "response": body,
            "severity": transparency["severity"],
            "transparency": transparency,
        }
