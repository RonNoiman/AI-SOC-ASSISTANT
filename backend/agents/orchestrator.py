import os

from groq import Groq

from agents.network_agent import NetworkAgent
from agents.identity_agent import IdentityAgent
from agents.policy_agent import PolicyAgent

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


class Orchestrator:
    """Routes user queries to the appropriate specialist agent."""

    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
        self.agents = (
            {
                "network": NetworkAgent(self.client),
                "identity": IdentityAgent(self.client),
                "policy": PolicyAgent(self.client),
            }
            if self.client
            else {}
        )

    async def classify_query(self, query: str) -> str:
        """Use LLM to determine which agent should handle the query."""
        if not self.client:
            lowered = query.lower()
            if any(term in lowered for term in ("user", "auth", "access", "mfa", "ldap", "ad ")):
                return "identity"
            if any(term in lowered for term in ("policy", "compliance", "audit", "nist", "iso", "gdpr", "hipaa")):
                return "policy"
            return "network"

        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a SOC query classifier. Classify the user query into exactly one category:\n"
                        "- network: firewall rules, IP addresses, ports, traffic, network segmentation\n"
                        "- identity: users, authentication, permissions, AD/LDAP, access reviews\n"
                        "- policy: compliance, security policies, frameworks, regulations, audits\n\n"
                        "Respond with only the category name, nothing else."
                    ),
                },
                {"role": "user", "content": query},
            ],
            temperature=0,
            max_tokens=10,
        )
        category = response.choices[0].message.content.strip().lower()
        return category if category in self.agents else "network"

    async def handle(self, query: str, conversation_history: list[dict] | None = None) -> dict:
        """Route query to the right agent and return the response."""
        agent_name = await self.classify_query(query)
        if self.client:
            agent = self.agents[agent_name]
            response = await agent.run(query, conversation_history or [])
        else:
            response = (
                "The backend is running, but Groq is not configured yet. "
                "Set GROQ_API_KEY in backend/.env to enable AI responses."
            )
        return {
            "agent": agent_name,
            "response": response,
        }
