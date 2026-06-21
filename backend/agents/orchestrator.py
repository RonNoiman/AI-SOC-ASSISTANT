import logging
import os

from agents.network_agent import NetworkAgent
from agents.identity_agent import IdentityAgent
from agents.policy_agent import PolicyAgent
from risk.evidence_correlator import EvidenceCorrelator

logger = logging.getLogger("soc.orchestrator")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def _build_client():
    """Return a Groq client if configured, else None (demo mode)."""
    if not GROQ_API_KEY:
        return None
    try:
        from groq import Groq

        return Groq(api_key=GROQ_API_KEY)
    except Exception as exc:
        logger.warning("Groq client init failed, falling back to demo mode: %s", exc)
        return None


def _keyword_classify(query: str) -> str:
    lowered = query.lower()
    # Policy is checked first because policy questions often include words like
    # "user" or "account" that would otherwise trip the identity bucket.
    policy_terms = (
        "policy", "policies", "compliance", "audit", "nist", "iso 27001", "iso27001",
        "gdpr", "hipaa", "soc 2", "regulation", "regulatory", "allowed to",
        "are we allowed", "incident response plan", "internal procedure",
    )
    identity_terms = (
        "login", "logon", "auth", "password", "credential", "mfa", "2fa",
        "sso", "ldap", "active directory", "okta", "entra", "azure ad",
        "brute force", "lockout", "failed login",
    )
    if any(term in lowered for term in policy_terms):
        return "policy"
    if any(term in lowered for term in identity_terms):
        return "identity"
    return "network"


class Orchestrator:
    """Routes user queries to the appropriate specialist agent."""

    def __init__(self):
        self.client = _build_client()
        self.correlator = EvidenceCorrelator(kb_dir="../knowledge_base")
        self.agents = {

            "network": NetworkAgent(self.client),
            "identity": IdentityAgent(self.client),
            "policy": PolicyAgent(self.client),
        }

    async def classify_query(self, query: str) -> str:
        """Determine which agent should handle the query."""
        if not self.client:
            return _keyword_classify(query)

        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a SOC query classifier. Classify the user query into exactly one category:\n"
                            "- network: firewall rules, IP addresses, ports, traffic, network segmentation, scans, suspicious connections\n"
                            "- identity: users, authentication, permissions, AD/LDAP, MFA, failed logins, credential issues\n"
                            "- policy: compliance, security policies, frameworks, regulations, audits, allowed/not-allowed questions\n\n"
                            "Respond with only the category name, nothing else."
                        ),
                    },
                    {"role": "user", "content": query},
                ],
                temperature=0,
                max_tokens=10,
            )
            category = response.choices[0].message.content.strip().lower()
            return category if category in self.agents else _keyword_classify(query)
        except Exception as exc:
            logger.warning("LLM classification failed, using keyword fallback: %s", exc)
            return _keyword_classify(query)

    async def handle(self, query: str, conversation_history: list[dict] | None = None) -> dict:
        """Route query to the right agent and return its structured triage result.

        Returns ``{"agent": name, "response": markdown, "severity": level}``.
        """
        agent_name = await self.classify_query(query)
        agent = self.agents[agent_name]
        logger.info("ROUTE category=%s query_preview=%r", agent_name, query[:80])
        result = await agent.run(query, conversation_history or [])
        transparency = result.get("transparency", {})
        logger.info(
            "TRIAGE agent=%s severity=%s threat_id=%s confidence=%.2f",
            agent_name,
            result["severity"],
            transparency.get("threat_id"),
            transparency.get("confidence_score", 0.0),
        )
        # --- RISK REASONING ENGINE OVERRIDE ---
        try:
            analysis = self.correlator.correlate_and_analyze(query)
            risk = analysis["risk"]
            phase = analysis["phase"]
            techniques = analysis["techniques"]
            context = analysis["context"]
            
            # Create Mermaid Graph
            phases = ["Recon", "Initial Access", "DMZ/VPN Exploit", "Lateral Movement", "Target Selection", "Command Execution", "Modem Management Exploit", "Wiper Deployment", "Impact"]
            phase_num = phase["phase_number"] if phase else 0
            phase_title = phase["phase_title"] if phase else "Unknown"
            
            graph = "```mermaid\ngraph LR\n"
            for i, phase_name in enumerate(phases):
                node_id = f"P{i+1}"
                style = ":::highlight" if (i + 1) == phase_num else ""
                graph += f"    {node_id}[\"{i+1}. {phase_name}\"]{style}\n"
                if i > 0:
                    graph += f"    P{i} --> P{i+1}\n"
            graph += "\n    classDef highlight fill:#f96,stroke:#333,stroke-width:4px;\n```"

            mitre_table = "### MITRE ATT&CK Mapping\n"
            mitre_table += "| Phase | Technique ID | Technique Name | Evidence | Confidence |\n"
            mitre_table += "|-------|--------------|----------------|----------|------------|\n"
            for t in techniques:
                mitre_table += f"| {t.get('attack_phase','')} | {t['technique_id']} | {t['technique_name']} | Matched input | {t.get('confidence_notes', 'N/A')} |\n"
            if not techniques:
                 mitre_table += "| N/A | N/A | No techniques mapped | N/A | N/A |\n"
                 
            risk_table = "### Risk Calculation\n"
            risk_table += "| Factor | Score | Reason | Evidence |\n"
            risk_table += "|--------|-------|--------|----------|\n"
            risk_table += f"| Likelihood | {risk['likelihood']}/5 | {', '.join(risk['likelihood_reasons'])} | {query} |\n"
            risk_table += f"| Impact | {risk['impact']}/5 | {', '.join(risk['impact_reasons'])} | Context inferred |\n"
            risk_table += f"| **Final Risk** | **{risk['risk_score']}/25** | **Likelihood x Impact** | **Severity: {risk['severity']}** |\n"

            # Strip old conflicting MITRE mapping from the LLM response
            import re
            enhanced_response = result["response"]
            enhanced_response = re.sub(r'### MITRE ATT&CK Mapping.*?###', '###', enhanced_response, flags=re.DOTALL)
            
            enhanced_response += f"\n\n### Attack Vector Context\n**Current Suspected Phase:** {phase_num} - {phase_title}\n\n{graph}\n\n{mitre_table}\n\n{risk_table}\n"
            
            if context.missing_info:
                 enhanced_response += "\n### Missing Context Information\n"
                 for m in context.missing_info:
                     enhanced_response += f"- {m}\n"
            
            final_severity = risk["severity"]
            transparency["severity"] = final_severity
            transparency["threat_id"] = "Deterministic Risk Engine"
            transparency["stride_category"] = "Multiple Contexts" 
            
        except Exception as e:
            logger.error(f"Risk engine failed: {e}")
            enhanced_response = result["response"]
            final_severity = result["severity"]
        # --------------------------------------

        return {
            "agent": agent_name,
            "response": enhanced_response,
            "severity": final_severity,
            "transparency": transparency,
        }

