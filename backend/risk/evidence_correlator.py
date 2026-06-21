from risk.mitre_mapper import MitreMapper
from risk.context_model import IncidentContext
from risk.risk_engine import RiskEngine

class EvidenceCorrelator:
    def __init__(self, kb_dir="knowledge_base"):
        self.mapper = MitreMapper(kb_dir=kb_dir)
        self.risk_engine = RiskEngine()

    def correlate_and_analyze(self, raw_input: str):
        # 1. Parse Context
        context = IncidentContext(raw_input=raw_input, observed_evidence=[raw_input])
        context.enrich_from_text()
        
        # 2. Map MITRE
        matched_techniques = self.mapper.map_techniques(raw_input)
        
        # 3. Infer Attack Phase
        inferred_phase = self.mapper.infer_phase(matched_techniques, raw_input)
        
        # 4. Calculate Risk
        risk_result = self.risk_engine.calculate_risk(context, matched_techniques, inferred_phase)
        
        # 5. Formulate Missing Info
        missing_info = []
        if not context.is_production and not context.is_test and "production" not in raw_input.lower() and "test" not in raw_input.lower():
            missing_info.append("Is this a production or test asset?")
            
        if inferred_phase and inferred_phase.get("phase_number") == 2:
            missing_info.extend([
                "Was the login authorized?",
                "Which account was used?",
                "Was MFA passed?",
                "Is there evidence of valid account abuse?",
                "Is there evidence of lateral movement?",
                "Are there repeated attempts from suspicious IPs?"
            ])
            
        if not context.valid_account_used and "T1078" not in raw_input and inferred_phase and inferred_phase.get("phase_number", 0) > 2:
             missing_info.append("Is there any evidence of valid account usage?")
             
        if inferred_phase and inferred_phase.get("phase_number", 0) > 2 and not context.lateral_movement:
            missing_info.append("Have you checked for lateral movement logs?")
            
        context.missing_info = missing_info
        
        return {
            "context": context,
            "techniques": matched_techniques,
            "phase": inferred_phase,
            "risk": risk_result
        }
