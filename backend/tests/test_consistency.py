import unittest
from risk.evidence_correlator import EvidenceCorrelator
from agents.orchestrator import Orchestrator

class TestConsistency(unittest.TestCase):
    def setUp(self):
        self.orchestrator = Orchestrator()
        self.correlator = self.orchestrator.correlator

    def test_simple_network_scan(self):
        result = self.correlator.correlate_and_analyze("We see a high volume of port connection attempts from an external IP T1595.002")
        self.assertIn("T1595.002", [t["technique_id"] for t in result["techniques"]])
        self.assertEqual(result["phase"]["phase_number"], 1)
        # Should be Low to Medium severity
        self.assertIn(result["risk"]["severity"], ["Low", "Medium"])
        
    def test_wiper_behavior_production(self):
        result = self.correlator.correlate_and_analyze("Mass file deletions observed on production servers. Wipe detected. T1561")
        self.assertIn("T1561", [t["technique_id"] for t in result["techniques"]])
        self.assertEqual(result["phase"]["phase_number"], 9)
        self.assertEqual(result["risk"]["severity"], "Critical")
        
    def test_supply_chain_compromise(self):
        result = self.correlator.correlate_and_analyze("Malicious updates deployed via trusted tools. T1195")
        self.assertIn("T1195", [t["technique_id"] for t in result["techniques"]])
        self.assertEqual(result["phase"]["phase_number"], 8)
        self.assertIn(result["risk"]["severity"], ["High", "Critical"])

    def test_same_technique_different_context(self):
        res1 = self.correlator.correlate_and_analyze("T1133 External Remote Services accessed")
        res2 = self.correlator.correlate_and_analyze("T1133 External Remote Services accessed on production gateway with valid account T1078 and lateral movement")
        
        # Risk score 2 should be higher due to context
        self.assertTrue(res2["risk"]["risk_score"] > res1["risk"]["risk_score"])
        self.assertTrue(res2["risk"]["impact"] > res1["risk"]["impact"])


    def test_t1133_isolated_test_machine_maps_to_phase_2_not_phase_7(self):
        result = self.correlator.correlate_and_analyze("We saw VPN logins using External Remote Services T1133 on an isolated test machine.")
        self.assertEqual(result["phase"]["phase_number"], 2)
        
    def test_t1133_isolated_test_machine_has_low_impact(self):
        result = self.correlator.correlate_and_analyze("We saw VPN logins using External Remote Services T1133 on an isolated test machine.")
        self.assertEqual(result["risk"]["impact"], 1)
        self.assertEqual(result["risk"]["severity"], "Low")
        
    def test_known_test_asset_not_asked_as_missing_context(self):
        result = self.correlator.correlate_and_analyze("isolated test machine T1133")
        self.assertTrue(result["context"].is_test)
        self.assertNotIn("Is this a production or test asset?", result["context"].missing_info)
        self.assertIn("Was the login authorized?", result["context"].missing_info)
        
    def test_phase_7_requires_modem_management_evidence(self):
        res1 = self.correlator.correlate_and_analyze("T1133 login")
        res2 = self.correlator.correlate_and_analyze("T1133 login to modem management interface")
        self.assertEqual(res1["phase"]["phase_number"], 2)
        self.assertEqual(res2["phase"]["phase_number"], 7)

if __name__ == '__main__':
    unittest.main()
