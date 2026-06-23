# AI SOC Assistant - Final Presentation

## Slide 1: Title + Team
**Title**: AI SOC Assistant: Multi-Agent Triage Platform
**Team**: Maor Kurztag, Roi Noiman, Daniel Gorodnitskiy
**Visual**: Project Logo / Minimalist Cyber/AI Graphic.
**Speaker Notes**: Welcome everyone. Today we are presenting the AI SOC Assistant, our final project demonstrating the integration of multi-agent LLM architectures into cybersecurity operations.

## Slide 2: Problem
**Title**: The Problem: Alert Fatigue
- SOC analysts face overwhelming volumes of security alerts.
- Triage requires manual correlation across disjointed logs.
- High burnout rates and delayed incident response.
**Visual**: A graphic showing a frustrated analyst drowning in logs.
**Speaker Notes**: Modern SOCs generate thousands of alerts daily. Analysts must manually sift through logs, extract IPs, and guess the severity, which creates a massive bottleneck.

## Slide 3: Project Goal
**Title**: Project Goal
- Automate Tier 1 alert triage using AI.
- Parse raw logs into structured intelligence (IOCs, MITRE mapping).
- Provide a secure, guardrailed interface for analysts.
**Visual**: Flow showing "Raw Log" -> "AI Assistant" -> "Structured Report".
**Speaker Notes**: Our goal is to build a web-based assistant that takes raw, messy log data and instantly returns a structured, severity-rated triage report, allowing analysts to focus on remediation.

## Slide 4: System Architecture
**Title**: System Architecture
- **Frontend**: React, TypeScript, Vite
- **Backend**: FastAPI (Python)
- **Database**: SQLite + SQLAlchemy
- **Security**: JWT Auth, Passlib
**Visual**: High-level block diagram of React -> FastAPI -> DB & LLM.
**Speaker Notes**: We chose a modern, decoupled architecture. A React frontend communicates securely via a FastAPI backend, which handles authentication and database persistence.

## Slide 5: Multi-Agent Flow
**Title**: Multi-Agent Flow
- **Orchestrator Agent**: Classifies user intent.
- **Specialized Agents**: Network, Identity, Policy.
- Reduces hallucinations by restricting agent scope.
**Visual**: Diagram showing Orchestrator routing to the three sub-agents.
**Speaker Notes**: We don't use just one generic AI prompt. We use an Orchestrator pattern. The user talks to the Orchestrator, which invisibly routes the request to a domain expert agent.

## Slide 6: SOC Analyst Workflow
**Title**: SOC Analyst Workflow
- Paste raw alert or natural language question.
- Receive immediate severity rating (Low, Medium, High, Critical).
- Review extracted IOCs and recommended playbooks.
**Visual**: Screenshot of the Chat interface showing a parsed alert.
**Speaker Notes**: The analyst simply pastes an alert into the chat. The assistant extracts the malicious IPs, assigns a severity, and provides a step-by-step mitigation playbook.

## Slide 7: MITRE ATT&CK and Supply Chain
**Title**: Knowledge Base Integration
- System checks against internal JSON dictionaries.
- Maps attacks to MITRE ATT&CK techniques.
- Evaluates supply chain risks.
**Visual**: Snippet of the JSON knowledge base and the resulting output in chat.
**Speaker Notes**: To ground the AI in reality, the agents are instructed to map identified threats to our internal MITRE and Supply Chain knowledge bases, ensuring standardized reporting.

## Slide 8: Risk & Severity Reasoning
**Title**: Risk & Severity Reasoning
- Deterministic guardrails combined with LLM analysis.
- Considers source reputation, target value, and attack stage.
- Ensures consistency in alert prioritization.
**Visual**: A risk matrix (Likelihood vs Impact) highlighting critical severity.
**Speaker Notes**: The agents don't just guess severity; they use an internal reasoning model assessing the attack stage and potential impact before assigning a final Risk Level.

## Slide 9: Guardrails and Protection
**Title**: Guardrails & Prompt Injection Protection
- **Input Guardrails**: Scans for "jailbreak" or "ignore previous instructions".
- **Output Guardrails**: Prevents the AI from generating harmful scripts.
- Admin-managed policies.
**Visual**: Flowchart of a user prompt hitting the guardrail block.
**Speaker Notes**: Because LLMs are vulnerable to prompt injection, our backend intercepts all messages. If an analyst—or an attacker—tries to manipulate the prompt, the guardrail blocks the request entirely.

## Slide 10: Demo Scenarios
**Title**: Demo Scenarios
- 1. Network Alert Analysis
- 2. Identity Brute Force Triage
- 3. Prompt Injection Block
**Visual**: Split-screen screenshots or video placeholders for each scenario.
**Speaker Notes**: We will now demonstrate the system live. First, we'll analyze a firewall log. Next, an identity alert. Finally, we'll try to hack our own system with a prompt injection and watch the guardrails stop it.

## Slide 11: Security Analysis / STRIDE
**Title**: Security Analysis (STRIDE)
- **Spoofing**: Mitigated by robust JWT auth.
- **Tampering**: Guardrails protect AI instructions.
- **Repudiation**: Comprehensive Audit Logs tracking routing and blocks.
**Visual**: STRIDE table highlighting mitigations.
**Speaker Notes**: We performed a STRIDE threat model on our application. The major risks—prompt tampering and unauthorized access—are mitigated by our guardrails and JWT authentication layer.

## Slide 12: Testing and Validation
**Title**: Testing and Validation
- Pytest framework for backend logic.
- Unit testing of Auth, Routing, and Guardrails.
- Confirmed deterministic routing across 50+ test prompts.
**Visual**: Screenshot of a passing Pytest terminal output.
**Speaker Notes**: Quality assurance is critical. We built an automated test suite verifying that authentication works, that the Orchestrator routes correctly, and that guardrails reliably catch malicious inputs.

## Slide 13: Limitations
**Title**: Limitations
- Requires manual log pasting (no real-time SIEM integration).
- SQLite database limits horizontal scalability.
- Dependent on external Groq API latency.
**Visual**: Bullet list with caution icons.
**Speaker Notes**: In its current MVP state, analysts must manually paste logs. Furthermore, we are using SQLite for simplicity, which isn't suitable for massive enterprise concurrency.

## Slide 14: Future Work
**Title**: Future Work
- Webhook integrations for automatic alert ingestion.
- Migration to PostgreSQL.
- Deployment of localized open-weights models (Ollama/vLLM).
**Visual**: A roadmap timeline graphic.
**Speaker Notes**: To take this to production, we would integrate directly with SIEM APIs to process alerts automatically and switch to local, self-hosted LLMs to ensure zero data leaves the corporate network.

## Slide 15: Summary
**Title**: Summary
- AI SOC Assistant accelerates incident triage.
- Multi-agent architecture provides specialized, accurate insights.
- Built-in guardrails ensure robust application security.
**Visual**: Group photo or project logo with "Q&A".
**Speaker Notes**: Thank you for your time. The AI SOC Assistant proves that multi-agent LLM systems can drastically reduce SOC analyst workload while maintaining strict security boundaries. We'll now take any questions.