from groq import Groq

SYSTEM_PROMPT = """You are a Network Security Agent in a SOC (Security Operations Center).
You specialize in:
- Firewall rule analysis and recommendations
- Network traffic analysis
- IP address and port investigations
- Network segmentation advice
- Intrusion detection/prevention guidance

Provide clear, actionable answers. When suggesting firewall rules, use standard notation.
Always consider security best practices and the principle of least privilege."""


class NetworkAgent:
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
