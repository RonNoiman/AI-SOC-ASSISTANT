from agents.base import BaseAgent


class PolicyAgent(BaseAgent):
    """SOC specialist for policy & compliance questions: frameworks, audits, risk."""

    domain_name = "Security Policy & Compliance"
    specialties = (
        "- Security policy creation and review\n"
        "- Compliance frameworks (NIST, ISO 27001, SOC 2, GDPR, HIPAA)\n"
        "- Audit preparation and evidence gathering\n"
        "- Risk assessment and management\n"
        "- Regulatory requirements interpretation"
    )
    refusal_clause = (
        "Refuse to advise on actions that would clearly violate policy, regulation, "
        "or user safety."
    )

    demo_summary = (
        "A policy or compliance question was received and triaged by the "
        "Security Policy & Compliance Agent."
    )
    demo_actions = [
        "Refer to the internal incident-response policy and the relevant control "
        "framework (NIST 800-61, ISO 27035).",
        "Document the decision, who approved it, and the justification (audit trail).",
        "Where the policy is ambiguous, escalate to security leadership / legal before acting.",
        "Preserve evidence (logs, account states) before making changes.",
        "After the incident, review whether the policy needs to be tightened or clarified.",
    ]
    demo_escalation = (
        "Notify the SOC lead; involve security leadership or legal/compliance when "
        "the policy is ambiguous or a regulatory obligation is in question."
    )
    demo_severity = "Informational"
