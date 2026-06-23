# AI SOC Assistant - Project One-Pager

## Project Title
AI SOC Assistant

## Team Members
- Maor Kurztag
- Roi Noiman
- Daniel Gorodnitskiy

## Problem Statement
Security Operations Center (SOC) analysts suffer from alert fatigue. They are bombarded with raw logs and alerts from various tools (firewalls, EDR, identity providers) and must manually correlate data, classify risk, and determine mitigation paths. This manual triage is slow and error-prone, leading to delayed incident response times.

## Proposed Solution
The AI SOC Assistant is a multi-agent AI application designed to augment Tier 1 and Tier 2 SOC analysts. By pasting raw logs or natural language queries into a secure chat interface, the system automatically classifies the intent and routes the query to a specialized AI agent (Network, Identity, or Policy). The agent parses the data, extracts Indicators of Compromise (IOCs), maps the threat to MITRE ATT&CK techniques, and delivers a structured severity-rated triage report.

## Architecture Summary
- **Frontend**: React + TypeScript + Vite
- **Backend**: Python + FastAPI
- **Database**: SQLite + SQLAlchemy
- **AI Layer**: Multi-Agent Orchestrator (Groq LLM API with fallback demo mode)
- **Security Layer**: JWT Authentication, PBKDF2 Password Hashing, Input/Output Guardrails.

## Main Features
- **Multi-Agent Triage**: Orchestrator dynamically routes requests to the best domain expert.
- **Knowledge Base Integration**: Analyzes alerts against internal JSON knowledge bases covering MITRE ATT&CK and Supply Chain attack vectors.
- **Chat Interface & History**: Allows analysts to converse iteratively and review past investigations.
- **Admin Dashboard**: Manages users, views system audit logs, and toggles custom guardrail rules.

## Security Focus
The system applies strict security boundaries:
- **Authentication & RBAC**: Differentiates between 'analyst' and 'admin' roles.
- **Input/Output Guardrails**: Proactively scans and blocks prompt injection, off-topic requests, and system-prompt extraction attempts.
- **Audit Logging**: Logs critical application events (logins, blocks, routing decisions) for non-repudiation.

## Innovation / AI Usage
Instead of a single monolithic prompt, the application uses an **Agentic Orchestrator Pattern**. The Orchestrator does not answer queries directly; it classifies the intent and delegates to specialized agents with narrowly scoped system prompts. This reduces hallucination and ensures responses adhere strictly to the specialized domain (e.g., Network vs. Identity).

## Technologies
React, TypeScript, FastAPI, SQLite, SQLAlchemy, Groq (Llama-3), JWT, Pytest.

## Expected Impact
Reduces the Mean Time To Triage (MTTT) by parsing unstructured data into structured intelligence instantly. It enables junior analysts to perform at a higher level by providing immediate, context-aware playbooks mapped to industry frameworks.

## Future Work
- Direct API integration with SIEM platforms (e.g., Splunk, Microsoft Sentinel) for automated log ingestion.
- Transitioning the backend database from SQLite to PostgreSQL for high concurrency.
- Migration to self-hosted LLMs (e.g., via Ollama) to guarantee complete data privacy for highly classified environments.