# AI SOC Assistant - Risk Reasoning Model

## Overview
The Risk Reasoning Model was designed to explain *why* an incident is assigned a specific severity, addressing the limitation of black-box LLM predictions.

## Context Enrichment
1. **Asset Context**: Determines if the asset is production, externally facing, and its data sensitivity.
2. **Behavioral Evidence**: Extracts indicators of lateral movement, valid account usage, firewall impairment, and destructive behavior from the raw alert.

## MITRE ATT&CK Mapping
The engine maps observed evidence to structured MITRE technique entries, determining the tactical goal and specific attack phase.

## Likelihood x Impact Calculation
- **Likelihood (1-5)**: Scales based on the number of confirmed techniques, external exposure, use of valid accounts, and defense impairment.
- **Impact (1-5)**: Scales based on asset criticality (e.g., production environments), evidence of lateral movement, and late-stage attack phases (e.g., wiper malware or supply chain deployment).

### Risk Score = Likelihood × Impact
- **1-4**: Low
- **5-9**: Medium
- **10-16**: High
- **17-25**: Critical

## Output Visualization
The model integrates a Mermaid-based Attack Flow graph to visually represent the suspected current phase within the broader attack context. This grounds the AI's answer in an understandable, deterministic framework.
