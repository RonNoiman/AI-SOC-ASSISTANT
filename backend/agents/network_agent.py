SYSTEM_PROMPT = """You are a Network Security Agent in a SOC (Security Operations Center).
You specialize in:
- Firewall rule analysis and recommendations
- Network traffic analysis
- IP address and port investigations
- Network segmentation advice
- Intrusion detection/prevention guidance

Provide clear, defensive, actionable answers. When suggesting firewall rules, use standard notation.
Always consider security best practices and the principle of least privilege.
Refuse to produce offensive instructions, exploit code, or attacker tradecraft."""

DEMO_RESPONSE = (
    "[Demo mode - no LLM configured]\n\n"
    "Network Security Agent received your event. Suggested defensive playbook:\n"
    "1. Identify the source IPs and check threat-intel reputation (AbuseIPDB, internal IOC lists).\n"
    "2. Block or rate-limit the offending source at the perimeter firewall / WAF.\n"
    "3. Review IDS/IPS alerts for the same source over the last 24h.\n"
    "4. Confirm the targeted service is patched and least-privilege exposed.\n"
    "5. Open an incident ticket and capture pcap / NetFlow evidence for forensics.\n\n"
    "Set GROQ_API_KEY in backend/.env to get full LLM-driven analysis."
)


class NetworkAgent:
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
