# AI SOC Assistant - Documentation

## Security analysis (for the cybersecurity presentation)

- [Security Analysis – STRIDE & Risk Matrix](security-analysis.md) — full
  STRIDE breakdown tied to real components, Risk Matrix with likelihood ×
  impact for every cataloged threat, residual risk and Future Improvement
  items flagged honestly.
- [Guardrails – Worked Examples](guardrails.md) — what each input/output
  guardrail blocks, why it is dangerous, what the user sees, and what is
  written to the audit log. Includes live evidence captured from the running
  backend.
- [Security Validation & Testing Report](security-testing.md) — 31-test
  pytest manifest with PASS/FAIL, plus a category matrix mapping the
  academic requirements to the tests that cover them.

## API Endpoints

### Auth
- `POST /auth/register` - create new user account
- `POST /auth/login` - get JWT access token
- `GET /auth/me` - get current user info

### Chat
- `POST /api/chat/` - send a message and get AI response (returns triage
  severity and the full AI Decision Reasoning transparency record)

### Conversations
- `GET /api/conversations/` - list user's conversations (search + filter
  by agent / severity / time)
- `GET /api/conversations/{id}/messages` - get messages for a conversation
- `DELETE /api/conversations/{id}` - delete a conversation

### Reference (Knowledge Base)
- `GET /api/reference/severity` - severity dictionary (Critical … Informational)
- `GET /api/reference/threats` - threat catalog (T1 … T8)
- `GET /api/reference/stride` - STRIDE × component analysis
- `GET /api/reference/risk-matrix` - Risk Matrix rows

### Admin
- `GET /api/admin/stats` - system statistics (admin only)
- `GET /api/admin/users` - list all users (admin only)
- `GET /api/admin/security-events` - audit log (admin only)
- `GET /api/admin/guardrail-policies` - admin-managed guardrail patterns

## Agent Routing

The orchestrator uses an LLM classifier to route queries:

| Category | Agent | Handles |
|----------|-------|---------|
| network | NetworkAgent | Firewall, traffic, IPs, ports |
| identity | IdentityAgent | Users, auth, AD/LDAP, MFA |
| policy | PolicyAgent | Compliance, frameworks, audits |
