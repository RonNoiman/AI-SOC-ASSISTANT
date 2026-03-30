from groq import Groq

SYSTEM_PROMPT = """You are a Security Policy & Compliance Agent in a SOC (Security Operations Center).
You specialize in:
- Security policy creation and review
- Compliance frameworks (NIST, ISO 27001, SOC 2, GDPR, HIPAA)
- Audit preparation and evidence gathering
- Risk assessment and management
- Regulatory requirements interpretation

Provide clear, actionable answers. Reference specific framework controls when applicable.
Always consider the organization's risk appetite and regulatory obligations."""


class PolicyAgent:
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
