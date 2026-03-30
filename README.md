# AI SOC Assistant

An AI-powered Security Operations Center assistant that uses specialized agents to help analysts with network security, identity & access management, and compliance/policy questions.

## Architecture

- **Orchestrator** — classifies incoming queries and routes them to the appropriate specialist agent
- **Network Agent** — firewall rules, traffic analysis, IP investigations
- **Identity Agent** — authentication, access reviews, AD/LDAP, MFA
- **Policy Agent** — compliance frameworks, security policies, audits
- **Guardrails** — input/output validation to prevent prompt injection and data leakage

## Tech Stack

- **Backend:** FastAPI + SQLAlchemy + PostgreSQL
- **LLM:** Groq (Llama 3.3 70B)
- **Auth:** JWT with bcrypt password hashing
- **Frontend:** React (coming soon)

## Getting Started

```bash
cd backend
cp .env.example .env   # fill in your keys
pip install -r requirements.txt
uvicorn main:app --reload
```

API docs available at `http://localhost:8000/docs`

## Running Tests

```bash
cd backend
pytest tests/
```
