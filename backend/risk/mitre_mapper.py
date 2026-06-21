import json
import yaml
import os

class MitreMapper:
    def __init__(self, kb_dir="knowledge_base"):
        self.kb_dir = kb_dir
        self.techniques = self._load_techniques()
        self.attack_flow = self._load_attack_flow()

    def _load_techniques(self):
        path = os.path.join(self.kb_dir, "mitre_techniques.json")
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            return []

    def _load_attack_flow(self):
        path = os.path.join(self.kb_dir, "attack_vectors", "vpn_modem_wiper_flow.yaml")
        try:
            with open(path, "r") as f:
                return yaml.safe_load(f)
        except Exception:
            return {"phases": []}

    def map_techniques(self, raw_input: str):
        text = raw_input.lower()
        matched = []
        for tech in self.techniques:
            # Simple keyword matching for demo purposes
            if tech["technique_id"].lower() in text or tech["technique_name"].lower() in text:
                matched.append(tech)
            else:
                for obs in tech.get("related_observables", []):
                    if obs.lower() in text:
                        matched.append(tech)
                        break
        return matched

    def infer_phase(self, matched_techniques, raw_input=""):
        if not matched_techniques:
            return None
            
        tech_ids = [t["technique_id"] for t in matched_techniques]
        text = raw_input.lower()
        
        possible_phases = []
        for phase in self.attack_flow.get("phases", []):
            overlap = set(phase.get("mitre_techniques", [])).intersection(set(tech_ids))
            if overlap:
                possible_phases.append(phase)
                
        if not possible_phases:
            return None
            
        possible_phases.sort(key=lambda x: x.get("phase_number", 0))
        
        # Rule-based escalation: default to earliest matching phase
        selected_phase = possible_phases[0]
        
        # Look for explicit justification to escalate to later phases
        for phase in possible_phases:
            p_num = phase.get("phase_number", 0)
            if p_num == 7 and any(kw in text for kw in ["modem", "management", "gateway center"]):
                selected_phase = phase
            elif p_num == 3 and any(kw in text for kw in ["dmz", "internal", "privilege escalation"]):
                selected_phase = phase
            elif p_num >= 8 and any(kw in text for kw in ["wiper", "delete", "destroy", "supply chain"]):
                selected_phase = phase
                
        return selected_phase
