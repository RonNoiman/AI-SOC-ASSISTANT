import logging
import re

logger = logging.getLogger("soc.agent")

MODEL = "llama-3.3-70b-versatile"

# SOC-standard severity ladder, highest to lowest.
VALID_SEVERITIES = ("Critical", "High", "Medium", "Low", "Informational")
DEFAULT_SEVERITY = "Medium"

# Appended to every agent's system prompt so all three specialists return the
# same triage shape: a parseable severity line followed by structured Markdown.
STRUCTURED_OUTPUT_INSTRUCTION = """
Always structure your answer in GitHub-flavored Markdown with these sections,
in this exact order:

SEVERITY: <one of: Critical | High | Medium | Low | Informational>

### Summary
One or two plain-language sentences describing what is happening.

### Indicators of Compromise (IOCs)
Bullet list of concrete IOCs you can extract from the event - IP addresses,
domains, file hashes, usernames, ports. If none are present, write
"None identified".

### MITRE ATT&CK Mapping
The most relevant ATT&CK technique(s) as `Txxxx - Name`. If it cannot be
determined, write "Not determined".

### Recommended Actions
A numbered list of concrete, defensive next steps for the analyst.

### Escalation Path
Who to notify and when (for example: SOC lead, incident response team,
asset owner).

Rules:
- The very first line MUST be `SEVERITY: <level>` and nothing else.
- Choose severity from the analyst's point of view: business impact x likelihood.
- Stay strictly defensive. Never produce offensive tradecraft, exploit code,
  or attacker steps.
""".strip()


def extract_severity(text: str) -> tuple[str, str]:
    """Split a model response into (severity, body).

    The agents are instructed to start their reply with a `SEVERITY: <level>`
    line. We parse and strip that line so the UI can render severity as a
    badge instead of leaving it in the prose. Falls back to a Medium severity
    and the untouched text if the model did not follow the format.
    """
    match = re.match(r"\s*SEVERITY:\s*([A-Za-z]+)\s*\n?", text)
    if match:
        level = match.group(1).strip().capitalize()
        if level in VALID_SEVERITIES:
            return level, text[match.end():].lstrip()

    # Be forgiving: scan the first few lines for a severity keyword.
    for line in text.splitlines()[:3]:
        for level in VALID_SEVERITIES:
            if re.search(rf"\bseverity\b.*\b{level}\b", line, re.I):
                return level, text

    return DEFAULT_SEVERITY, text


class BaseAgent:
    """Shared behaviour for the three SOC specialist agents.

    Subclasses only declare their domain-specific prompt content and demo-mode
    playbook; the LLM call, structured-output contract, and severity parsing
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

    def _demo_response(self) -> str:
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

    async def run(self, query: str, history: list[dict]) -> dict:
        """Return ``{"response": markdown, "severity": level}``."""
        if self.client is None:
            return {"response": self._demo_response(), "severity": self.demo_severity}

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
            return {"response": self._demo_response(), "severity": self.demo_severity}

        severity, body = extract_severity(raw)
        return {"response": body, "severity": severity}
