"""Risk Intelligence Dictionary - analyst-facing meaning of every severity level.

Used by the Knowledge Base page and by the in-Chat transparency panel to answer
"why this severity, why not higher, why not lower" without the analyst having to
guess what the model meant.
"""

SEVERITY_LEVELS: list[dict] = [
    {
        "level": "Critical",
        "color": "#dc2626",
        "what_it_means": (
            "Confirmed or near-certain compromise with immediate business impact. "
            "Active attacker, active data loss, or active service outage."
        ),
        "typical_indicators": [
            "Active C2 communication observed",
            "Confirmed credential compromise on a privileged account",
            "Ransomware encryption in progress",
            "Confirmed data exfiltration to an external destination",
        ],
        "typical_scenarios": [
            "Domain admin account taken over with an active session",
            "Ransomware spreading laterally across file shares",
            "Active SQL exfiltration from a production database",
        ],
        "why_dangerous": (
            "Every minute increases blast radius. Requires immediate containment, "
            "executive notification, and incident-response activation."
        ),
        "why_not_higher": "Critical is the top of the ladder.",
        "why_not_lower": (
            "High implies 'significant potential impact' but no confirmed compromise. "
            "Critical requires confirmed compromise or active damage."
        ),
        "response_sla": "Engage IR immediately; executive notification within 15 minutes.",
    },
    {
        "level": "High",
        "color": "#ea580c",
        "what_it_means": (
            "Suspicious activity with strong evidence of malicious intent and "
            "significant potential business impact, but no confirmed compromise yet."
        ),
        "typical_indicators": [
            "Multiple corroborating malicious indicators on one entity",
            "Source IP on a high-reputation threat-intel feed",
            "Repeated failed-then-successful login from an unusual geo",
            "Privilege change on a sensitive account outside change window",
        ],
        "typical_scenarios": [
            "Brute-force followed by a successful login from a new country",
            "Privileged-group membership change with no approval ticket",
            "Sustained reconnaissance against an internet-facing admin portal",
        ],
        "why_dangerous": (
            "Strong signal that an attack is in progress or imminent. Demands "
            "analyst attention now, not later in the queue."
        ),
        "why_not_higher": "Critical requires confirmed compromise; High has strong suspicion only.",
        "why_not_lower": (
            "Medium implies ambiguous signal that could be benign. High has multiple "
            "indicators all pointing the same direction."
        ),
        "response_sla": "Analyst engagement within 30 minutes.",
    },
    {
        "level": "Medium",
        "color": "#ca8a04",
        "what_it_means": (
            "Notable activity that warrants investigation but may have a benign "
            "explanation. Single indicator or low-confidence signal."
        ),
        "typical_indicators": [
            "Single failed-login burst from a known geo",
            "Internal port scan that may be authorized vulnerability scanning",
            "Configuration drift on a non-critical asset",
        ],
        "typical_scenarios": [
            "Unfamiliar process running on a development workstation",
            "One unusual outbound flow that could be a legitimate update",
        ],
        "why_dangerous": (
            "Could be early-stage attack or a noisy false-positive - only "
            "investigation decides which. Not safe to ignore."
        ),
        "why_not_higher": "High requires multiple corroborating signals or a threat-intel match.",
        "why_not_lower": (
            "Low implies known-benign or expected behavior. Medium still has open "
            "questions that need answering."
        ),
        "response_sla": "Analyst review within 4 hours.",
    },
    {
        "level": "Low",
        "color": "#16a34a",
        "what_it_means": (
            "Event of interest with low likelihood of malicious intent - typically "
            "expected or already-known behavior worth recording."
        ),
        "typical_indicators": [
            "Expected scheduled scan from a known security tool",
            "One-off failed login with immediate user-driven recovery",
            "Minor policy deviation with documented business justification",
        ],
        "typical_scenarios": [
            "Authorized vulnerability scan triggering IDS",
            "User typed the wrong password once, then logged in correctly",
        ],
        "why_dangerous": (
            "Mostly noise, but a pattern of Low events on the same entity over "
            "time can re-classify upward."
        ),
        "why_not_higher": "No corroborating malicious indicators present.",
        "why_not_lower": "Informational implies purely operational, with no security relevance.",
        "response_sla": "Reviewed during the next shift turnover.",
    },
    {
        "level": "Informational",
        "color": "#0284c7",
        "what_it_means": (
            "Operational event with no malicious signal. Recorded for traceability "
            "and context, not for analyst action."
        ),
        "typical_indicators": [
            "Successful login from a known device and known location",
            "Compliance question with no detected event",
            "Routine policy lookup",
        ],
        "typical_scenarios": [
            "Analyst asks 'are we allowed to do X under GDPR?'",
            "Routine audit-evidence query",
        ],
        "why_dangerous": "Not dangerous - recorded for completeness.",
        "why_not_higher": "No security signal at all; this is operational context.",
        "why_not_lower": "Informational is the floor.",
        "response_sla": "No action required.",
    },
]


def get_level(name: str | None) -> dict | None:
    if not name:
        return None
    target = name.strip().capitalize()
    for entry in SEVERITY_LEVELS:
        if entry["level"] == target:
            return entry
    return None
