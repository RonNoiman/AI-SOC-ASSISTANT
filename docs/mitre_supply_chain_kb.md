# Knowledge Base: MITRE & Supply Chain Attack Integration

## MITRE ATT&CK Techniques
The Knowledge Base (`mitre_techniques.json`) contains structured entries for techniques used in the reference Attack Flow (e.g., T1595.002, T1133, T1078, T1195, T1561).
Each entry provides:
- Technique ID & Name
- Tactic & Attack Phase
- Defensive Explanation
- Related Observables & Likelihood/Impact indicators
- Relevant Mitigations

## Supply Chain Attack Integration
Supply chain compromises (T1195) are integrated into Phase 8 of the reference attack flow. 
Our model understands that:
- Supply chain attacks bypass traditional perimeters.
- They abuse implicit trust.
- They result in a massive blast radius.
- When `T1195` is detected, the impact score is maximized due to the late attack stage and severe consequences.

## The Reference Attack Flow
The 9-Phase VPN/Modem Wiper flow is defined in `attack_vectors/vpn_modem_wiper_flow.yaml`. It provides the engine with a roadmap to contextualize isolated alerts.