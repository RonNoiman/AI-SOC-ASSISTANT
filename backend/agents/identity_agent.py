from agents.base import BaseAgent


class IdentityAgent(BaseAgent):
    """SOC specialist for identity & access events: auth, AD/LDAP, MFA, privileges."""

    domain_name = "Identity & Access Management"
    specialties = (
        "- User authentication and authorization issues\n"
        "- Active Directory / LDAP queries and troubleshooting\n"
        "- Access reviews and privilege escalation detection\n"
        "- MFA and SSO configuration guidance\n"
        "- Identity governance and lifecycle management"
    )
    refusal_clause = (
        "Refuse to produce credential-theft tooling, password-cracking guidance, "
        "or any offensive tradecraft."
    )

    demo_summary = (
        "An identity or authentication event was received and triaged by the "
        "Identity & Access Management Agent."
    )
    demo_actions = [
        "Lock or temporarily disable the targeted account(s) and force a password reset.",
        "Require MFA re-enrollment for the affected user.",
        "Check geo / impossible-travel anomalies in the SIEM (Okta / Azure AD / Entra logs).",
        "Pull recent privilege changes; revoke any unexpected role assignments.",
        "Notify the user out-of-band and open an incident ticket.",
    ]
    demo_escalation = (
        "Notify the SOC lead; escalate to the IAM team and the user's manager if "
        "account compromise is confirmed."
    )
    demo_severity = "High"
    demo_threat_id = "T2"  # Credential Stuffing / Brute Force is the canonical demo case.
    demo_stride = "Spoofing"
    demo_confidence = 0.78
    demo_indicators = [
        "Multiple failed logins on the same account",
        "Authentication attempts from rotating source IPs",
        "Short time window between attempts",
    ]
    demo_reasoning = (
        "Pattern matches credential-stuffing / brute-force behaviour against a "
        "single identity; severity is High because successful takeover would "
        "expose the analyst's data, but compromise is not yet confirmed."
    )
    demo_recommended_action = (
        "Lock or temporarily disable the targeted account and require MFA "
        "re-enrollment before re-enabling."
    )
