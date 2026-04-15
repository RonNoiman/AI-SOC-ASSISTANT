# AI SOC Assistant

AI SOC Assistant is a multi-agent cybersecurity assistant designed to support Security Operations Center (SOC) workflows. The system classifies incoming questions, routes them to a relevant specialist agent, applies basic safety checks, and stores conversation history for authenticated users.

This project combines a **FastAPI backend**, a **React + Vite frontend**, **PostgreSQL** persistence, and **Groq-hosted LLMs** to deliver a focused security assistant instead of a generic chatbot.

---

## Table of Contents

- [Project Goal](#project-goal)
- [Core Capabilities](#core-capabilities)
- [System Architecture](#system-architecture)
- [How It Works](#how-it-works)
- [Agent Routing Model](#agent-routing-model)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Database Design](#database-design)
- [Authentication and Authorization](#authentication-and-authorization)
- [Guardrails](#guardrails)
- [API Overview](#api-overview)
- [Local Setup](#local-setup)
- [Running the Project](#running-the-project)
- [Testing](#testing)
- [Known Limitations](#known-limitations)
- [Future Improvements](#future-improvements)
- [Contributors](#contributors)

---

## Project Goal

Traditional SOC teams deal with many categories of questions:

- Network investigations
- Identity and access issues
- Security policy and compliance questions

A single generic chatbot can answer these unevenly. AI SOC Assistant addresses that by introducing an **orchestrator** that decides which specialist agent should handle each request.

The current project focuses on four main ideas:

1. **Intent classification** for cybersecurity-related requests
2. **Routing to specialist agents** based on domain
3. **Basic safety validation** for user input and model output
4. **Conversation persistence** for authenticated users

---

## Core Capabilities

### Backend capabilities

- User registration and login
- JWT-based authentication
- Conversation creation and message persistence
- Domain-based routing through an orchestrator
- Admin endpoints for system visibility
- Health endpoint for service checks

### Frontend capabilities

- Login page
- Register page
- Protected chat interface
- Conversation history page
- Admin page

### AI capabilities

- Multi-agent routing
- Domain specialization:
  - **Network Agent**
  - **Identity Agent**
  - **Policy Agent**
- Basic input and output guardrails

---

## System Architecture

```mermaid
flowchart TD
    U[User] --> FE[React Frontend]
    FE -->|HTTP / JSON| BE[FastAPI Backend]
    BE --> AUTH[Auth Layer]
    BE --> GR[Guardrails]
    BE --> ORCH[Orchestrator]

    ORCH --> N[Network Agent]
    ORCH --> I[Identity Agent]
    ORCH --> P[Policy Agent]

    BE --> DB[(PostgreSQL)]
    N --> LLM[Groq LLM]
    I --> LLM
    P --> LLM

    DB --> BE
    BE --> FE
    FE --> U
```

### Architecture summary

- The **frontend** provides the user-facing interface.
- The **backend** handles authentication, routing, validation, and persistence.
- The **orchestrator** chooses the most relevant specialist agent.
- The **database** stores users, conversations, and messages.
- The **LLM layer** generates the agent response.

---

## How It Works

```mermaid
sequenceDiagram
    autonumber
    participant User
    participant Frontend
    participant Backend
    participant Guardrails
    participant Orchestrator
    participant Agent
    participant DB
    participant Groq

    User->>Frontend: Submit message
    Frontend->>Backend: POST /api/chat/
    Backend->>Guardrails: Validate input
    Guardrails-->>Backend: Safe / blocked

    alt blocked input
        Backend-->>Frontend: Validation error
    else safe input
        Backend->>Orchestrator: Classify request
        Orchestrator->>Agent: Route to selected specialist
        Agent->>Groq: Generate response
        Groq-->>Agent: Draft answer
        Agent-->>Backend: Final response
        Backend->>Guardrails: Validate output
        Guardrails-->>Backend: Safe / blocked
        Backend->>DB: Save user message + assistant response
        Backend-->>Frontend: Return response
    end

    Frontend-->>User: Show answer
```

---

## Agent Routing Model

The assistant uses an orchestrator to classify each query into one of the supported categories.

| Category | Agent | Typical Topics |
|---|---|---|
| `network` | Network Agent | Firewall rules, traffic analysis, ports, IP investigation |
| `identity` | Identity Agent | Authentication, AD/LDAP, MFA, access reviews |
| `policy` | Policy Agent | Security policies, compliance frameworks, audits |

### Routing concept

```mermaid
flowchart LR
    Q[Incoming Query] --> C{Classifier}
    C -->|network| N[Network Agent]
    C -->|identity| I[Identity Agent]
    C -->|policy| P[Policy Agent]
```

This approach keeps answers more focused than a single-agent design and makes the system easier to extend later with additional expert agents.

---

## Technology Stack

### Backend

- **FastAPI**
- **SQLAlchemy**
- **PostgreSQL**
- **python-jose** for JWT handling
- **passlib + bcrypt** for password hashing
- **python-dotenv** for configuration
- **Groq SDK** for LLM access

### Frontend

- **React**
- **TypeScript**
- **Vite**
- **React Router**

### Testing

- **pytest**
- **httpx**

---

## Project Structure

```text
AI-SOC-ASSISTANT/
├── backend/
│   ├── api/
│   │   ├── admin.py
│   │   ├── chat.py
│   │   └── conversations.py
│   ├── auth/
│   │   └── router.py
│   ├── database/
│   │   ├── connection.py
│   │   └── models.py
│   ├── guardrails/
│   │   └── checker.py
│   ├── tests/
│   ├── .env.example
│   ├── main.py
│   └── requirements.txt
├── docs/
│   └── README.md
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── context/
│   │   ├── pages/
│   │   │   ├── Login.tsx
│   │   │   ├── Register.tsx
│   │   │   ├── Chat.tsx
│   │   │   ├── History.tsx
│   │   │   └── Admin.tsx
│   │   └── App.tsx
│   └── package.json
└── README.md
```

> Note: The exact file list may evolve, but this reflects the structure used by the current implementation.

---

## Database Design

The system currently uses three main entities:

- **User**
- **Conversation**
- **Message**

```mermaid
erDiagram
    USER ||--o{ CONVERSATION : owns
    CONVERSATION ||--o{ MESSAGE : contains

    USER {
        int id PK
        string email
        string hashed_password
        string full_name
        string role
        boolean is_active
        datetime created_at
    }

    CONVERSATION {
        int id PK
        string title
        int user_id FK
        datetime created_at
        datetime updated_at
    }

    MESSAGE {
        int id PK
        int conversation_id FK
        string role
        text content
        string agent_used
        datetime created_at
    }
```

### Data model rationale

- A **User** can own multiple conversations.
- A **Conversation** contains an ordered list of messages.
- A **Message** may record which agent produced the response.

This design is simple, readable, and suitable for an MVP.

---

## Authentication and Authorization

The application uses **JWT-based authentication**.

### Auth flow

```mermaid
flowchart TD
    A[Register or Login] --> B[Backend validates credentials]
    B --> C[JWT access token issued]
    C --> D[Frontend stores token]
    D --> E[Authenticated API requests]
    E --> F[Protected routes and user-specific data]
```

### Current auth-related features

- Register new users
- Login with credentials
- Access current user profile via token
- Restrict protected routes to authenticated users
- Admin-only endpoints for selected operations

---

## Guardrails

The project includes a basic guardrail layer for both input and output validation.

### Input checks

The input validation currently aims to block:

- Prompt injection attempts
- Requests to ignore system instructions
- Role-jailbreak style prompts
- Clearly off-topic queries

### Output checks

The output validation currently aims to block:

- Obvious secret leakage patterns
- Sensitive data patterns such as passwords or secrets

### Guardrail position in the pipeline

```mermaid
flowchart LR
    IN[User Input] --> GI[Input Guardrails]
    GI --> ORCH[Orchestrator + Agent]
    ORCH --> GO[Output Guardrails]
    GO --> OUT[Final Response]
```

> Important: these guardrails are a **basic first layer**, not a complete production-grade security boundary.

---

## API Overview

### Authentication

- `POST /auth/register` — create a new user account
- `POST /auth/login` — authenticate and receive JWT token
- `GET /auth/me` — get current user details

### Chat

- `POST /api/chat/` — send a message and receive an AI response

### Conversations

- `GET /api/conversations/` — list the current user's conversations
- `GET /api/conversations/{id}/messages` — get messages for a conversation
- `DELETE /api/conversations/{id}` — delete a conversation

### Admin

- `GET /api/admin/stats` — admin-only system statistics
- `GET /api/admin/users` — admin-only user list

### Utility

- `GET /health` — service health check

### Interactive API docs

Once the backend is running, Swagger UI is available at:

```text
http://localhost:8000/docs
```

---

## Local Setup

### Prerequisites

Make sure you have the following installed:

- **Python 3.10+**
- **Node.js 18+**
- **npm**
- **PostgreSQL**
  - or Docker, if you prefer running PostgreSQL in a container
- **Groq API key**

### Environment variables

Create a `.env` file inside `backend/` based on `.env.example`:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/soc_assistant
SECRET_KEY=your-secret-key-here
GROQ_API_KEY=your-groq-api-key-here
```

---

## Running the Project

## 1. Start PostgreSQL

You can either use a local installation or Docker.

### Option A — local PostgreSQL

Create a database called `soc_assistant` and update `DATABASE_URL` accordingly.

### Option B — PostgreSQL with Docker

```bash
docker run --name soc-postgres \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=soc_assistant \
  -p 5432:5432 \
  -d postgres
```

## 2. Run the backend

```bash
cd backend
python -m venv .venv
```

### Windows

```bash
.venv\Scripts\activate
```

### macOS / Linux

```bash
source .venv/bin/activate
```

Then install dependencies and start FastAPI:

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Backend should be available at:

```text
http://localhost:8000
```

## 3. Run the frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Vite usually starts at:

```text
http://localhost:5173
```

---

## Important Development Note

The backend CORS configuration currently allows `http://localhost:3000`, while Vite commonly runs on `http://localhost:5173`.

If the frontend cannot call the backend due to CORS, update the backend configuration accordingly.

Example:

```python
allow_origins=["http://localhost:3000", "http://localhost:5173"]
```

---

## Testing

Backend tests can be run with:

```bash
cd backend
pytest tests/
```

Current tests appear to focus mainly on backend logic and authentication-related behavior.

---

## Known Limitations

This project is a strong MVP, but it is not yet a full production SOC platform.

### Current limitations

- Guardrails are rule-based and basic
- No live SIEM integration
- No real log ingestion pipeline
- No RAG pipeline or enterprise knowledge base
- No Docker Compose setup for one-command deployment
- No CI/CD pipeline defined in the repository
- Frontend is functional but still lightweight in polish
- Session handling and admin controls appear minimal

---

## Future Improvements

Recommended next steps for the project:

1. Add **Dockerfiles** for backend and frontend
2. Add **docker-compose.yml** for full local orchestration
3. Introduce **role-based access control** beyond basic admin separation
4. Connect to **real SOC data sources** such as SIEM alerts or knowledge bases
5. Add **RAG retrieval** for internal policies and documentation
6. Expand **automated testing** with integration and end-to-end coverage
7. Improve **frontend UX** for analysts working across longer conversations
8. Add **audit logging** and observability metrics

---

## Contributors

Example team roles for academic presentation:

- **Maor Kurztag** — architecture, backend core, orchestration
- **Roi Noiman** — database, backend logic, testing
- **Daniel Gorodnitskiy** — frontend, diagrams, integration, documentation

---

## Final Notes

AI SOC Assistant is best described as a **multi-agent cybersecurity MVP**.

Its strengths are:

- Clear domain focus
- Good separation of responsibilities
- Simple and understandable data model
- Real full-stack structure instead of a single demo script

Its current maturity level is best presented as:

- **Working academic project**
- **Proof-of-concept product**
- **Foundation for future SOC automation features**

