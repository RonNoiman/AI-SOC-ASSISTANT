# AI SOC Assistant - Documentation

## API Endpoints

### Auth
- `POST /auth/register` - create new user account
- `POST /auth/login` - get JWT access token
- `GET /auth/me` - get current user info

### Chat
- `POST /api/chat/` - send a message and get AI response

### Conversations
- `GET /api/conversations/` - list user's conversations
- `GET /api/conversations/{id}/messages` - get messages for a conversation
- `DELETE /api/conversations/{id}` - delete a conversation

### Admin
- `GET /api/admin/stats` - system statistics (admin only)
- `GET /api/admin/users` - list all users (admin only)

## Agent Routing

The orchestrator uses an LLM classifier to route queries:

| Category | Agent | Handles |
|----------|-------|---------|
| network | NetworkAgent | Firewall, traffic, IPs, ports |
| identity | IdentityAgent | Users, auth, AD/LDAP, MFA |
| policy | PolicyAgent | Compliance, frameworks, audits |
