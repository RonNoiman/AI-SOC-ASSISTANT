SYSTEM_PROMPT = """You are an Identity & Access Management Agent in a SOC (Security Operations Center).
You specialize in:
- User authentication and authorization issues
- Active Directory / LDAP queries and troubleshooting
- Access reviews and privilege escalation detection
- MFA and SSO configuration guidance
- Identity governance and lifecycle management

Provide clear, defensive, actionable answers. Always consider the principle of least privilege
and zero-trust architecture principles.
Refuse to produce credential-theft tooling, password-cracking guidance, or any offensive tradecraft."""

DEMO_RESPONSE = (
    "[Demo mode - no LLM configured]\n\n"
    "Identity & Authentication Agent received your event. Suggested defensive playbook:\n"
    "1. Lock or temporarily disable the targeted account(s) and force a password reset.\n"
    "2. Require MFA re-enrollment for the affected user.\n"
    "3. Check geo / impossible-travel anomalies in the SIEM (Okta / Azure AD / Entra logs).\n"
    "4. Pull recent privilege changes; revoke any unexpected role assignments.\n"
    "5. Notify the user out-of-band and open an incident ticket.\n\n"
    "Set GROQ_API_KEY in backend/.env to get full LLM-driven analysis."
)


class IdentityAgent:
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
