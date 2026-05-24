"""STRIDE x component threat model for the AI SOC Assistant.

Each STRIDE category ties to one or more concrete attack scenarios against a
real component of this codebase. For each scenario we record the existing
mitigation in the code and the residual risk that remains - honest about what
the project does NOT yet defend against (flagged as Future Improvement).
"""

STRIDE_ANALYSIS: list[dict] = [
    {
        "category": "Spoofing",
        "definition": "Pretending to be another user or system.",
        "scenarios": [
            {
                "attack": (
                    "Attacker submits a victim's email plus a guessed password to "
                    "POST /auth/login to take over the analyst session."
                ),
                "affected_component": "auth/service.py, auth/router.py",
                "risk": (
                    "Account takeover; access to the analyst's conversation history "
                    "and chat tools."
                ),
                "mitigation": (
                    "Passwords hashed with pbkdf2_sha256, account lockout after 5 "
                    "failed attempts, JWT bound per user, every login attempt recorded "
                    "in SecurityEvent (success or failure)."
                ),
                "residual_risk": (
                    "No MFA in the current build. If a password is leaked elsewhere "
                    "and the account is not yet locked, the first valid attempt "
                    "succeeds. Future Improvement: TOTP or WebAuthn second factor."
                ),
            },
            {
                "attack": (
                    "Attacker steals a JWT from a developer console and replays it "
                    "from another browser."
                ),
                "affected_component": "auth/middleware.py",
                "risk": "Session hijacking until the token expires.",
                "mitigation": (
                    "Bearer JWTs scoped to one user; admin actions re-check role from "
                    "the database, not from the token claim."
                ),
                "residual_risk": (
                    "No server-side revocation list - a leaked token remains valid "
                    "until natural expiry. Acceptable for the academic scope; "
                    "Future Improvement: add a revocation table keyed by jti."
                ),
            },
        ],
    },
    {
        "category": "Tampering",
        "definition": "Modifying data or behavior maliciously.",
        "scenarios": [
            {
                "attack": (
                    "Analyst (or external attacker with a session) injects "
                    "instructions in the chat to override the agent system prompt "
                    "and produce offensive tradecraft."
                ),
                "affected_component": "guardrails/checker.py, agents/base.py",
                "risk": (
                    "AI produces attacker content; the system loses its defensive "
                    "posture (covered by threat catalog entry T1)."
                ),
                "mitigation": (
                    "Regex input guardrail blocks the request before any LLM call; "
                    "user receives a refusal and a guardrail strike is recorded. "
                    "Three strikes lock the account."
                ),
                "residual_risk": (
                    "Pattern-based detection can miss novel paraphrasings. The output "
                    "guardrail provides a second layer for sensitive-content leakage. "
                    "Future Improvement: classifier-based prompt-injection detector."
                ),
            },
            {
                "attack": (
                    "Authenticated user calls /api/conversations/{id} for a "
                    "conversation that belongs to another user."
                ),
                "affected_component": "api/conversations.py",
                "risk": "Information disclosure or destructive modification across tenants.",
                "mitigation": (
                    "Every conversation query filters by user_id from the JWT; "
                    "mismatches return 404."
                ),
                "residual_risk": "None observed in the current code path.",
            },
        ],
    },
    {
        "category": "Repudiation",
        "definition": "Denying an action when there is no evidence to the contrary.",
        "scenarios": [
            {
                "attack": (
                    "User denies submitting a malicious prompt that was blocked, "
                    "or denies that a routing decision was theirs."
                ),
                "affected_component": "auth/service.py (SecurityEvent), api/chat.py",
                "risk": "Without an audit trail, abuse cannot be proven.",
                "mitigation": (
                    "Every login attempt (success or failure), guardrail block, "
                    "routing decision, and chat message is written to SecurityEvent "
                    "with timestamp, user_id, email, IP, agent, severity, threat_id, "
                    "and confidence. The admin dashboard exposes the log."
                ),
                "residual_risk": (
                    "Logs live in the same SQLite database as the application. A "
                    "compromised database compromises the log. Future Improvement: "
                    "ship audit events to an append-only sink (e.g. Loki, S3 object lock)."
                ),
            },
        ],
    },
    {
        "category": "Information Disclosure",
        "definition": "Exposing data to unauthorized parties.",
        "scenarios": [
            {
                "attack": (
                    "Authenticated attacker tries to read another analyst's "
                    "conversations via /api/conversations/."
                ),
                "affected_component": "api/conversations.py",
                "risk": "Cross-tenant chat exposure.",
                "mitigation": "All queries filter on user_id from the JWT.",
                "residual_risk": "None observed in the current code path.",
            },
            {
                "attack": (
                    "An LLM response contains a value that looks like a credential "
                    "and the analyst sees it in chat or history."
                ),
                "affected_component": "guardrails/checker.py (check_output), api/chat.py",
                "risk": "Sensitive data leak from the LLM into the UI and persistence.",
                "mitigation": (
                    "Output guardrail scans for password / api-key patterns and "
                    "replaces the response if matched. Block is audited."
                ),
                "residual_risk": (
                    "Static regex misses encoded or novel secret formats. "
                    "Future Improvement: entropy-based scanner plus secret-format "
                    "library (e.g. TruffleHog-style detectors)."
                ),
            },
        ],
    },
    {
        "category": "Denial of Service",
        "definition": "Making the service unavailable to legitimate users.",
        "scenarios": [
            {
                "attack": (
                    "Attacker scripts thousands of failed logins to lock every "
                    "demo account."
                ),
                "affected_component": "auth/service.py - lockout logic",
                "risk": "Legitimate analysts cannot log in.",
                "mitigation": (
                    "Lockouts are per-account and unlockable by an admin from the "
                    "admin dashboard. Every attempt is logged so the source is visible."
                ),
                "residual_risk": (
                    "No global rate-limit middleware. Future Improvement: add an "
                    "IP-bucket rate limiter (e.g. slowapi) at the FastAPI layer."
                ),
            },
            {
                "attack": (
                    "Attacker submits a megabyte-long prompt to exhaust the LLM "
                    "token budget or backend memory."
                ),
                "affected_component": "api/chat.py - ChatRequest body",
                "risk": "Increased latency, token spend, or memory pressure.",
                "mitigation": (
                    "Pydantic body size is bounded by Uvicorn defaults; Groq "
                    "enforces token caps server-side."
                ),
                "residual_risk": (
                    "No explicit per-user message-length cap in app code. "
                    "Future Improvement: enforce max input length in ChatRequest."
                ),
            },
        ],
    },
    {
        "category": "Elevation of Privilege",
        "definition": "Gaining rights beyond those granted.",
        "scenarios": [
            {
                "attack": (
                    "Non-admin analyst calls /api/admin/users to escalate "
                    "themselves to admin."
                ),
                "affected_component": "api/admin.py - get_current_admin dependency",
                "risk": "Full takeover of user, policy, and log management.",
                "mitigation": (
                    "Every admin route depends on get_current_admin, which "
                    "re-checks user.role == 'admin' from the database, not from "
                    "the token claim."
                ),
                "residual_risk": (
                    "None observed for the current admin endpoints; new endpoints "
                    "must reuse the same dependency."
                ),
            },
            {
                "attack": (
                    "Analyst crafts a prompt that asks the LLM to 'grant' admin "
                    "privileges or reveal admin-only data."
                ),
                "affected_component": "guardrails/checker.py + agents/base.py",
                "risk": (
                    "Trust-boundary confusion between AI reasoning and authorization."
                ),
                "mitigation": (
                    "Authorization is enforced at the API layer (RBAC), not by the "
                    "LLM. The LLM has no ability to mutate roles. The input guardrail "
                    "blocks role-rebind prompts."
                ),
                "residual_risk": "Acceptable by design - the LLM has no authority.",
            },
        ],
    },
]


RISK_MATRIX: list[dict] = [
    {
        "threat_id": "T1",
        "threat": "Prompt Injection / Jailbreak",
        "stride": "Tampering",
        "likelihood": "High",
        "impact": "Medium",
        "severity": "High",
        "affected_component": "Guardrail / LLM",
        "mitigation": "Regex input guardrail + 3-strike account lockout + output guardrail.",
        "residual_risk": "Pattern-based detector can miss novel paraphrasings.",
        "why_this_severity": (
            "High likelihood because LLMs are well-known injection targets; impact "
            "is bounded to AI behaviour (Medium) because authorization is enforced "
            "at the API layer, not by the LLM."
        ),
    },
    {
        "threat_id": "T2",
        "threat": "Credential Stuffing / Brute Force",
        "stride": "Spoofing",
        "likelihood": "High",
        "impact": "High",
        "severity": "High",
        "affected_component": "auth/service.py",
        "mitigation": "Account lockout after 5 failed attempts; per-attempt audit log.",
        "residual_risk": "No global IP-rate-limit; lockout is per-account, not per-IP.",
        "why_this_severity": (
            "High likelihood (commodity attack); High impact because a successful "
            "takeover gives full session access to the analyst's data."
        ),
    },
    {
        "threat_id": "T3",
        "threat": "Reconnaissance / Port Scanning",
        "stride": "Information Disclosure",
        "likelihood": "Medium",
        "impact": "Low",
        "severity": "Medium",
        "affected_component": "External network (recommendation only)",
        "mitigation": "Network Agent recommends firewall and IDS rules; not enforced by the app.",
        "residual_risk": "App-level only; real enforcement is upstream.",
        "why_this_severity": (
            "Medium likelihood as background internet noise; Low direct impact on "
            "this app because it is not internet-exposed in the demo."
        ),
    },
    {
        "threat_id": "T4",
        "threat": "Privilege Escalation Attempt",
        "stride": "Elevation of Privilege",
        "likelihood": "Low",
        "impact": "High",
        "severity": "High",
        "affected_component": "api/admin.py",
        "mitigation": "Every admin route uses get_current_admin and re-reads the role from the DB.",
        "residual_risk": "Future admin endpoints must reuse the dependency or the door opens.",
        "why_this_severity": (
            "Low likelihood given strict RBAC; High impact because elevation grants "
            "full system access."
        ),
    },
    {
        "threat_id": "T5",
        "threat": "Insider Threat / Anomalous Access",
        "stride": "Information Disclosure",
        "likelihood": "Low",
        "impact": "High",
        "severity": "Medium",
        "affected_component": "All endpoints",
        "mitigation": "Audit log records every action with user_id and IP.",
        "residual_risk": (
            "No UEBA baseline; detection is by retrospective audit-log review only."
        ),
        "why_this_severity": (
            "Low likelihood in the academic deployment; impact is High in principle. "
            "Severity Medium because we have only retrospective detection."
        ),
    },
    {
        "threat_id": "T6",
        "threat": "Data Exfiltration",
        "stride": "Information Disclosure",
        "likelihood": "Low",
        "impact": "High",
        "severity": "Medium",
        "affected_component": "External network (recommendation only)",
        "mitigation": "Network Agent recommends DLP / egress filtering; not enforced by the app.",
        "residual_risk": "App is advisory; real enforcement is upstream.",
        "why_this_severity": (
            "Low likelihood that exfiltration occurs via this app (no PII store); "
            "High impact in principle."
        ),
    },
    {
        "threat_id": "T7",
        "threat": "Policy Violation / Compliance Gap",
        "stride": "Repudiation",
        "likelihood": "Medium",
        "impact": "Medium",
        "severity": "Medium",
        "affected_component": "Policy Agent + audit log",
        "mitigation": (
            "Policy Agent cites the relevant control and records who approved the "
            "decision; audit log preserves the trail."
        ),
        "residual_risk": "Reliant on the analyst documenting the decision honestly.",
        "why_this_severity": "Both likelihood and impact are operational, hence Medium.",
    },
    {
        "threat_id": "T8",
        "threat": "Malware / Suspicious Process",
        "stride": "Tampering",
        "likelihood": "Medium",
        "impact": "High",
        "severity": "High",
        "affected_component": "External endpoints (recommendation only)",
        "mitigation": "Network Agent recommends EDR quarantine + host isolation.",
        "residual_risk": "App is advisory; real enforcement is at the endpoint.",
        "why_this_severity": (
            "Medium likelihood at enterprise scale; High impact because a single "
            "infected host can pivot."
        ),
    },
]


def get_category(name: str | None) -> dict | None:
    if not name:
        return None
    target = name.strip().lower()
    for entry in STRIDE_ANALYSIS:
        if entry["category"].lower() == target:
            return entry
    return None
