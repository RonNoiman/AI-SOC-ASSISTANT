from agents.base import BaseAgent


class NetworkAgent(BaseAgent):
    """SOC specialist for network-layer events: firewalls, traffic, IPs, ports."""

    domain_name = "Network Security"
    specialties = (
        "- Firewall rule analysis and recommendations\n"
        "- Network traffic and NetFlow analysis\n"
        "- IP address and port investigations\n"
        "- Network segmentation advice\n"
        "- Intrusion detection/prevention guidance"
    )

    demo_summary = (
        "A network-layer security event was received and triaged by the "
        "Network Security Agent."
    )
    demo_actions = [
        "Identify the source IPs and check threat-intel reputation (AbuseIPDB, internal IOC lists).",
        "Block or rate-limit the offending source at the perimeter firewall / WAF.",
        "Review IDS/IPS alerts for the same source over the last 24h.",
        "Confirm the targeted service is patched and least-privilege exposed.",
        "Open an incident ticket and capture pcap / NetFlow evidence for forensics.",
    ]
    demo_escalation = (
        "Notify the SOC lead; escalate to the network/firewall team if active "
        "exploitation is confirmed."
    )
    demo_severity = "Medium"
