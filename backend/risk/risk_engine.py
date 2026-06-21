from risk.context_model import IncidentContext

class RiskEngine:
    def __init__(self):
        pass

    def calculate_risk(self, context: IncidentContext, matched_techniques: list, phase: dict):
        likelihood = 1
        impact = 1
        
        likelihood_reasons = []
        impact_reasons = []

        # Base likelihood from techniques
        if matched_techniques:
            likelihood = min(5, len(matched_techniques) + 1)
            likelihood_reasons.append(f"Matched {len(matched_techniques)} MITRE techniques.")
            
        # Context modifiers for likelihood
        if context.asset_context and context.asset_context.external_exposure:
            likelihood = min(5, likelihood + 1)
            likelihood_reasons.append("Asset has external exposure.")
            
        if context.valid_account_used:
            likelihood = min(5, likelihood + 2)
            likelihood_reasons.append("Valid accounts were used, increasing success probability.")
            
        if context.firewall_impaired:
            likelihood = min(5, likelihood + 2)
            likelihood_reasons.append("Defense impairment (firewall disabled) observed.")

        # Base impact from context
        if context.asset_context:
            impact_mod = context.asset_context.get_impact_modifier()
            impact = min(5, 1 + impact_mod)
            if context.is_test:
                impact = 1
                impact_reasons.append("Impact is strictly bounded because the asset is an isolated test machine.")
            elif impact_mod > 0:
                impact_reasons.append(f"Asset criticality ({context.asset_context.asset_criticality}) and sensitivity increased impact.")

        if context.is_production:
            impact = min(5, impact + 2)
            impact_reasons.append("Target is a production environment.")
            
        if context.lateral_movement:
            impact = min(5, impact + 1)
            impact_reasons.append("Lateral movement indicates wider blast radius.")
            
        if context.destructive_behavior:
            impact = 5
            likelihood = 5 # If destructive behavior is observed, it's definitely happening
            impact_reasons.append("Destructive behavior (wiper/deletion) directly causes maximum impact.")
            
        if phase and phase.get("phase_number", 0) >= 8:
             impact = 5
             impact_reasons.append("Attack has reached late stages (Phase 8+), maximizing potential impact.")

        risk_score = likelihood * impact
        
        severity = "Low"
        if risk_score >= 17:
            severity = "Critical"
        elif risk_score >= 10:
            severity = "High"
        elif risk_score >= 5:
            severity = "Medium"

        return {
            "likelihood": likelihood,
            "likelihood_reasons": likelihood_reasons,
            "impact": impact,
            "impact_reasons": impact_reasons,
            "risk_score": risk_score,
            "severity": severity
        }
