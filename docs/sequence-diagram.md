# Sequence Diagram

## Purpose

This sequence describes the main flow implemented and presented up to Sprint 4:

- User submits credentials
- Frontend sends request to backend
- Backend validates and authenticates the user
- Database is queried
- JWT token is returned
- User gains access to protected routes

---

## Login Flow Sequence Diagram

```mermaid
sequenceDiagram
    actor User
    participant Frontend
    participant Backend as FastAPI Backend
    participant Auth as Auth Service
    participant DB as PostgreSQL

    User->>Frontend: Enter login credentials
    Frontend->>Backend: POST /auth/login
    Backend->>Auth: Validate credentials
    Auth->>DB: Query user by email / username
    DB-->>Auth: Return stored user
    Auth->>Auth: Verify password
    Auth->>Auth: Generate JWT token
    Auth-->>Backend: Return authentication result
    Backend-->>Frontend: Return access token
    Frontend-->>User: Grant access to protected area
```

---

## Register Flow Sequence Diagram

```mermaid
sequenceDiagram
    actor User
    participant Frontend
    participant Backend as FastAPI Backend
    participant Auth as Auth Service
    participant DB as PostgreSQL

    User->>Frontend: Fill registration form
    Frontend->>Backend: POST /auth/register
    Backend->>Auth: Validate input data
    Auth->>DB: Check if user already exists
    DB-->>Auth: Return result
    Auth->>Auth: Hash password
    Auth->>DB: Create new user
    DB-->>Auth: Confirm creation
    Auth-->>Backend: Return created user
    Backend-->>Frontend: Return success response
    Frontend-->>User: Registration completed
```

---

## Why This Diagram Fits Sprint 4

This sequence is important because Sprint 4 is the stage where the system stops being only a structural prototype and begins behaving like a real application.

It demonstrates:

- frontend-backend communication
- authentication handling
- database usage
- protected access behavior

---

## Planned Future Sequence Extensions

Later milestones are expected to extend the flow with:

- chat request handling
- AI routing
- specialist agents
- conversation persistence
- guardrail checks

These are intentionally not part of the current milestone.
