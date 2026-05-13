SYSTEM_PROMPT = """You are a Security Policy & Compliance Agent in a SOC (Security Operations Center).
You specialize in:
- Security policy creation and review
- Compliance frameworks (NIST, ISO 27001, SOC 2, GDPR, HIPAA)
- Audit preparation and evidence gathering
- Risk assessment and management
- Regulatory requirements interpretation

Provide clear, defensive, actionable answers. Reference specific framework controls when applicable.
Always consider the organization's risk appetite and regulatory obligations.
Refuse to advise on actions that would clearly violate policy, regulation, or user safety."""

DEMO_RESPONSE = (
    "[Demo mode - no LLM configured]\n\n"
    "Policy & Compliance Agent received your question. General guidance:\n"
    "1. Refer to your internal incident-response policy and the relevant control framework (NIST 800-61, ISO 27035).\n"
    "2. Document the decision, who approved it, and the justification (audit trail).\n"
    "3. Where the policy is ambiguous, escalate to security leadership / legal before acting.\n"
    "4. Preserve evidence (logs, account states) before making changes.\n"
    "5. After the incident, review whether the policy needs to be tightened or clarified.\n\n"
    "Set GROQ_API_KEY in backend/.env to get full LLM-driven analysis."
)


class PolicyAgent:
    def __init__(self, client):
        self.client = client

    async def run(self, query: str, history: list[dict]) -> str:
        if self.client is None:
            return DEMO_RESPONSE

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend(history)
        messages.append({"role": "user", "content": query})

        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.3,
            max_tokens=2048,
        )
        return response.choices[0].message.content
