# Security Analysis – STRIDE & Risk Matrix

This document is the formal security analysis of the AI SOC Assistant. It
covers the threat model (STRIDE), the cataloged threats the system reasons
about (T1…T8), and the risk matrix that ties them together.

The same data is also available **inside the running app** under
**Knowledge Base → STRIDE Analysis / Risk Matrix / Threat Dictionary**, so the
analyst can pivot from a live triage straight to the rationale. The source of
truth for both is the Python data modules under `backend/data/`.

---

## 1. Method

We applied **STRIDE** (Spoofing, Tampering, Repudiation, Information
Disclosure, Denial of Service, Elevation of Privilege) to every trust boundary
in the actual codebase, not a generic system. Each scenario lists:

- the concrete attack against a named file / module,
- the risk if the attack succeeds,
- the mitigation **as it exists in code today**,
- the residual risk that remains, including items marked **Future Improvement**.

Residual risk is documented honestly – this is an academic project, not a
production system, and we mark gaps rather than pretend they are closed.

---

## 2. Threat catalog (T-IDs)

T-IDs follow the standard threat-model traceability notation. Every agent
response includes a `THREAT_ID` so an analyst can trace a triage back to a
known threat.

| ID | Threat | STRIDE | Primary agent |
|----|--------|--------|---------------|
| T1 | Prompt Injection / Jailbreak | Tampering | Guardrail |
| T2 | Credential Stuffing / Brute Force | Spoofing | Identity |
| T3 | Reconnaissance / Port Scanning | Information Disclosure | Network |
| T4 | Privilege Escalation Attempt | Elevation of Privilege | Identity |
| T5 | Insider Threat / Anomalous Access | Information Disclosure | Identity |
| T6 | Data Exfiltration | Information Disclosure | Network |
| T7 | Policy Violation / Compliance Gap | Repudiation | Policy |
| T8 | Malware / Suspicious Process | Tampering | Network |

Full descriptions, attack examples, detection indicators, and mitigations live
in `backend/data/threat_catalog.py` and at `GET /api/reference/threats`.

---

## 3. STRIDE analysis

### 3.1 Spoofing — *pretending to be another user or system*

**Scenario S-1.** Attacker submits a victim's email + a guessed password to
`POST /auth/login`.

- **Affected component:** `auth/service.py`, `auth/router.py`
- **Risk:** Account takeover; access to the analyst's conversation history.
- **Mitigation:** Passwords hashed with `pbkdf2_sha256`; account lockout after
  5 failed attempts; per-attempt entry written to `SecurityEvent` (success or
  failure); JWT bound per user.
- **Residual risk:** No MFA. **Future Improvement:** add a TOTP or WebAuthn
  second factor.

**Scenario S-2.** Attacker steals a JWT from a developer console and replays
it from another browser.

- **Affected component:** `auth/middleware.py`
- **Risk:** Session hijacking until natural token expiry.
- **Mitigation:** Tokens are bearer JWTs scoped to one user; admin actions
  re-check `user.role == 'admin'` from the database, not from the token claim.
- **Residual risk:** No server-side revocation list. **Future Improvement:**
  add a revocation table keyed by `jti`.

### 3.2 Tampering — *modifying data or behavior maliciously*

**Scenario T-1.** Authenticated user injects instructions in the chat to
override the agent's system prompt (Threat **T1**).

- **Affected component:** `guardrails/checker.py`, `agents/base.py`
- **Risk:** AI produces attacker content; defensive posture lost.
- **Mitigation:** Regex input guardrail blocks before the LLM is called;
  refusal + guardrail strike recorded; three strikes lock the account.
- **Residual risk:** Pattern-based detection can miss novel paraphrasings; the
  output guardrail provides a second layer for sensitive-content leakage.
  **Future Improvement:** classifier-based prompt-injection detector.

**Scenario T-2.** Authenticated user calls `/api/conversations/{id}` for a
conversation belonging to another user.

- **Affected component:** `api/conversations.py`
- **Risk:** Cross-tenant chat exposure or destructive modification.
- **Mitigation:** Every conversation query filters by `user_id` from the JWT;
  mismatches return 404.
- **Residual risk:** None observed in the current code path.

### 3.3 Repudiation — *denying an action with no evidence to the contrary*

**Scenario R-1.** User denies submitting a malicious prompt, or denies a
routing decision was theirs.

- **Affected component:** `auth/service.py` (`SecurityEvent`), `api/chat.py`
- **Risk:** Without an audit trail, abuse cannot be proven.
- **Mitigation:** Every login (success or failure), every guardrail block,
  every routing decision, every chat message is written to `SecurityEvent`
  with timestamp, `user_id`, email, IP, agent, severity, threat_id, and
  confidence. The admin dashboard exposes the full log.
- **Residual risk:** Logs live in the same SQLite database as the application.
  A compromised DB compromises the log. **Future Improvement:** ship audit
  events to an append-only sink (Loki, S3 object-lock, etc).

### 3.4 Information Disclosure — *exposing data to unauthorized parties*

**Scenario I-1.** Authenticated attacker tries to read another analyst's
conversations via `/api/conversations/`.

- **Affected component:** `api/conversations.py`
- **Risk:** Cross-tenant chat exposure.
- **Mitigation:** All queries filter on `user_id` from the JWT.
- **Residual risk:** None observed in the current code path.

**Scenario I-2.** An LLM response contains a value that looks like a
credential and the analyst sees it in chat or history.

- **Affected component:** `guardrails/checker.py` (`check_output`), `api/chat.py`
- **Risk:** Sensitive data leak from the LLM into UI and persistence.
- **Mitigation:** Output guardrail scans for password / api-key patterns and
  replaces the response if matched; block is audited.
- **Residual risk:** Static regex misses encoded or novel secret formats.
  **Future Improvement:** entropy-based scanner plus secret-format library
  (TruffleHog-style detectors).

### 3.5 Denial of Service — *making the service unavailable*

**Scenario D-1.** Attacker scripts thousands of failed logins to lock every
demo account.

- **Affected component:** `auth/service.py` – lockout logic
- **Risk:** Legitimate analysts cannot log in.
- **Mitigation:** Lockouts are per-account, time-limited, and unlockable by
  an admin from the admin dashboard; every attempt is logged.
- **Residual risk:** No global rate-limit middleware. **Future Improvement:**
  add an IP-bucket rate limiter (e.g. `slowapi`) at the FastAPI layer.

**Scenario D-2.** Attacker submits a megabyte-long prompt to exhaust the LLM
token budget or backend memory.

- **Affected component:** `api/chat.py` – `ChatRequest` body
- **Risk:** Increased latency, token spend, or memory pressure.
- **Mitigation:** Pydantic body size bounded by Uvicorn defaults; Groq enforces
  token caps server-side.
- **Residual risk:** No explicit per-user message-length cap in app code.
  **Future Improvement:** enforce `max_length` in `ChatRequest`.

### 3.6 Elevation of Privilege — *gaining rights beyond those granted*

**Scenario E-1.** Non-admin analyst calls `/api/admin/users` to escalate
themselves to admin.

- **Affected component:** `api/admin.py` – `get_current_admin` dependency
- **Risk:** Full takeover of user / policy / log management.
- **Mitigation:** Every admin route depends on `get_current_admin`, which
  re-checks `user.role == 'admin'` from the database, not from the token claim.
- **Residual risk:** None observed for existing admin endpoints; new endpoints
  must reuse the same dependency.

**Scenario E-2.** Analyst crafts a prompt that asks the LLM to "grant" admin
privileges or reveal admin-only data.

- **Affected component:** `guardrails/checker.py` + `agents/base.py`
- **Risk:** Trust-boundary confusion between AI reasoning and authorization.
- **Mitigation:** Authorization is enforced at the **API layer (RBAC)**, not by
  the LLM. The LLM has no ability to mutate roles. The input guardrail blocks
  role-rebind prompts.
- **Residual risk:** Acceptable by design – the LLM has no authority.

---

## 4. Risk Matrix

Likelihood × Impact = Severity for each catalogued threat.

| ID | Threat | STRIDE | Likelihood | Impact | Severity | Affected Component | Mitigation | Residual Risk | Why this severity |
|----|--------|--------|------------|--------|----------|--------------------|------------|---------------|--------------------|
| T1 | Prompt Injection / Jailbreak | Tampering | High | Medium | High | Guardrail / LLM | Regex input guardrail + 3-strike account lockout + output guardrail | Pattern-based detector can miss novel paraphrasings | High likelihood because LLMs are well-known injection targets; impact is bounded to AI behaviour because authorization is enforced at the API layer, not by the LLM |
| T2 | Credential Stuffing / Brute Force | Spoofing | High | High | High | `auth/service.py` | Account lockout after 5 failed attempts; per-attempt audit log | No global IP rate-limit; lockout is per-account, not per-IP | Commodity attack with full-takeover impact |
| T3 | Reconnaissance / Port Scanning | Information Disclosure | Medium | Low | Medium | External network (advisory) | Network Agent recommends firewall / IDS rules | App-level only; real enforcement upstream | Background internet noise; low direct impact on this app |
| T4 | Privilege Escalation Attempt | Elevation of Privilege | Low | High | High | `api/admin.py` | Every admin route uses `get_current_admin` and re-reads role from the DB | New admin endpoints must reuse the dependency | Low likelihood given strict RBAC; impact would be full takeover |
| T5 | Insider Threat / Anomalous Access | Information Disclosure | Low | High | Medium | All endpoints | Audit log records every action with `user_id` and IP | No UEBA baseline; retrospective detection only | High in principle; mitigation is retrospective so net severity is Medium |
| T6 | Data Exfiltration | Information Disclosure | Low | High | Medium | External network (advisory) | Network Agent recommends DLP / egress filtering | App is advisory; real enforcement upstream | No PII store inside this app |
| T7 | Policy Violation / Compliance Gap | Repudiation | Medium | Medium | Medium | Policy Agent + audit log | Policy Agent cites the controlling control; audit log preserves the trail | Reliant on analyst documenting decisions honestly | Both likelihood and impact are operational |
| T8 | Malware / Suspicious Process | Tampering | Medium | High | High | External endpoints (advisory) | Network Agent recommends EDR quarantine + host isolation | App is advisory; real enforcement at the endpoint | One infected host can pivot |

---

## 5. Trust boundaries diagram

```
                     ┌────────────────────────────────────────┐
                     │             SOC Analyst                │
                     └──────────────────┬─────────────────────┘
                                        │ HTTPS (local demo)
                          ┌─────────────▼──────────────┐
                          │   React frontend (Vite)    │
                          │   - stores JWT             │
                          └─────────────┬──────────────┘
                                        │ Bearer JWT
                          ┌─────────────▼──────────────┐
                          │  FastAPI backend           │
                          │  - auth/middleware.py      │  trust boundary: client → server
                          │  - api/admin re-checks role│  (RBAC enforced here, NOT in the LLM)
                          │  - guardrails/checker.py   │  trust boundary: user → LLM
                          │  - api/reference.py        │
                          └────────┬──────────────┬────┘
                                   │              │
                  ┌────────────────▼───┐   ┌──────▼────────────────┐
                  │  SQLite database    │   │  Groq LLM (optional)  │
                  │  - users            │   │  - llama-3.3-70b      │
                  │  - conversations    │   │  - cloud API          │
                  │  - messages         │   │  - no auth context    │
                  │  - security_events  │   │    crosses this line  │
                  │  - guardrail_policies│   └───────────────────────┘
                  └──────────────────────┘
```

Every arrow that crosses a trust boundary is covered by at least one mitigation
above. The LLM never sees auth state and has no authority to grant access — a
deliberate design choice that bounds the blast radius of any prompt-injection
success.

---

## 6. Scope and limitations

- This analysis covers the **AI SOC Assistant** application only, not the
  hosting environment.
- We do not analyse the security of Groq's hosted LLM beyond noting that
  authorization cannot cross the API boundary.
- "Future Improvement" items are honest deferrals, not promises; they are out
  of scope for the academic deliverable.

For the day-to-day evidence that these controls actually work (test inputs,
expected behaviour, PASS/FAIL), see [`security-testing.md`](security-testing.md).
For worked guardrail-block examples, see [`guardrails.md`](guardrails.md).
