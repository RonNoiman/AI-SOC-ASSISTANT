from typing import List, Dict, Any

class ContextModel:
    def __init__(self, asset_criticality: int, external_exposure: bool, business_function: str, data_sensitivity: str):
        self.asset_criticality = asset_criticality  # 1 to 5
        self.external_exposure = external_exposure
        self.business_function = business_function
        self.data_sensitivity = data_sensitivity
        
    def get_impact_modifier(self) -> int:
        modifier = 0
        if self.asset_criticality >= 4:
            modifier += 2
        elif self.asset_criticality == 3:
            modifier += 1
        if self.data_sensitivity.lower() in ["high", "critical", "pii", "phi"]:
            modifier += 1
        return modifier
        
    def get_likelihood_modifier(self) -> int:
        modifier = 0
        if self.external_exposure:
            modifier += 1
        return modifier

class IncidentContext:
    def __init__(self, raw_input: str, observed_evidence: List[str], missing_info: List[str] = None):
        self.raw_input = raw_input
        self.observed_evidence = observed_evidence
        self.missing_info = missing_info or []
        self.asset_context: ContextModel = None
        self.is_production = False
        self.is_test = False
        self.is_test = False
        self.is_test = False
        self.valid_account_used = False
        self.lateral_movement = False
        self.destructive_behavior = False
        self.firewall_impaired = False

    def enrich_from_text(self):
        text = self.raw_input.lower()
        if "production" in text or "prod" in text:
            self.is_production = True
        if "test" in text or "isolated" in text:
            self.is_test = True
        if "valid account" in text or "successful login" in text:
            self.valid_account_used = True
        if "lateral" in text or "psexec" in text or "smb" in text:
            self.lateral_movement = True
        if "wipe" in text or "delete" in text or "destroy" in text:
            self.destructive_behavior = True
        if "firewall" in text and ("disable" in text or "stop" in text or "modify" in text):
            self.firewall_impaired = True
            
        if not self.asset_context:
            crit = 5 if self.is_production else (1 if self.is_test else 2)
            sens = "High" if self.is_production else ("Low" if self.is_test else "Medium")
            self.asset_context = ContextModel(
                asset_criticality=crit,
                external_exposure="vpn" in text or "public" in text or "dmz" in text,
                business_function="Unknown",
                data_sensitivity=sens
            )
