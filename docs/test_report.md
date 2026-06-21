# Consistency Test Report

## Summary
To ensure the AI SOC Assistant does not provide inconsistent or context-blind answers, a deterministic risk engine was implemented and tested.

## Tests Performed
1. **Simple Network Scan (T1595.002)**
   - Expected: Phase 1, Low/Medium Severity
   - Result: PASS

2. **Wiper Behavior on Production (T1561)**
   - Expected: Phase 9, Critical Severity
   - Result: PASS

3. **Supply Chain Compromise (T1195)**
   - Expected: Phase 8, High/Critical Severity
   - Result: PASS

4. **Same Technique, Different Context (Context Awareness)**
   - Test: T1133 (External Remote Services) with no context vs. T1133 on production with valid accounts and lateral movement.
   - Expected: The second scenario must yield a significantly higher Risk Score and Impact.
   - Result: PASS. Context modifiers successfully incremented likelihood (valid accounts) and impact (production, lateral movement).

## Fixes Applied during Testing
- Initial logic failed to assign "Critical" severity to a wiper attack on production because the likelihood score remained too low to breach the 17-point threshold. We updated the logic to automatically raise Likelihood and Impact to 5 when destructive behavior (wiper/deletion) is confirmed, resulting in a 25/25 Critical score.