from groq import Groq

SYSTEM_PROMPT = """You are an Identity & Access Management Agent in a SOC (Security Operations Center).
You specialize in:
- User authentication and authorization issues
- Active Directory / LDAP queries and troubleshooting
- Access reviews and privilege escalation detection
- MFA and SSO configuration guidance
- Identity governance and lifecycle management

Provide clear, actionable answers. Always consider the principle of least privilege
and zero-trust architecture principles."""


class IdentityAgent:
    def __init__(self, client: Groq):
        self.client = client

    async def run(self, query: str, history: list[dict]) -> str:
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
