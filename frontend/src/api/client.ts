const API_BASE = "http://localhost:8000";

function formatApiError(detail: unknown, fallback: string): string {
  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }

  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (typeof item === "string") {
          return item;
        }
        if (item && typeof item === "object" && "msg" in item) {
          return String(item.msg);
        }
        return null;
      })
      .filter(Boolean);

    if (messages.length > 0) {
      return messages.join(". ");
    }
  }

  if (detail && typeof detail === "object" && "msg" in detail) {
    return String(detail.msg);
  }

  return fallback;
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = localStorage.getItem("token");
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...((options.headers as Record<string, string>) || {}),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (res.status === 401) {
    localStorage.removeItem("token");
    window.location.href = "/login";
    throw new Error("Unauthorized");
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(formatApiError(body.detail, `Request failed: ${res.status}`));
  }

  return res.json();
}

// Auth
export const auth = {
  login: (email: string, password: string) =>
    request<{ access_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  register: (email: string, password: string, full_name: string) =>
    request<{ access_token: string }>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name }),
    }),
  requestPasswordReset: (email: string) =>
    request<{ detail: string }>("/auth/forgot-password/request", {
      method: "POST",
      body: JSON.stringify({ email }),
    }),
  confirmPasswordReset: (token: string, new_password: string) =>
    request<{ detail: string }>("/auth/forgot-password/confirm", {
      method: "POST",
      body: JSON.stringify({ token, new_password }),
    }),
  me: () =>
    request<{ id: number; email: string; full_name: string | null; role: string }>("/auth/me"),
};

// Chat
export interface Transparency {
  severity: string;
  confidence_score: number;
  threat_id: string | null;
  stride_category: string | null;
  matched_indicators: string[];
  reasoning: string;
  recommended_action: string;
}

export const chat = {
  send: (message: string, conversation_id?: number) =>
    request<{
      response: string;
      agent: string;
      conversation_id: number;
      blocked?: boolean;
      severity: string | null;
      transparency: Transparency | null;
    }>("/api/chat/", {
      method: "POST",
      body: JSON.stringify({ message, conversation_id }),
    }),
};

// Conversations
export interface ConversationSummary {
  id: number;
  title: string;
  created_at: string;
  acknowledged: boolean;
  updated_at: string;
  message_count: number;
  agents: string[];
  top_severity: string | null;
}

export interface Message {
  id: number;
  role: string;
  content: string;
  agent_used: string | null;
  severity: string | null;
  transparency: Transparency | null;
  created_at: string;
  acknowledged: boolean;
}

export interface ConversationFilters {
  q?: string;
  agent?: string;
  severity?: string;
  sort?: "newest" | "oldest";
}

export const conversations = {
  list: (filters: ConversationFilters = {}) => {
    const params = new URLSearchParams();
    if (filters.q && filters.q.trim()) params.set("q", filters.q.trim());
    if (filters.agent) params.set("agent", filters.agent);
    if (filters.severity) params.set("severity", filters.severity);
    if (filters.sort) params.set("sort", filters.sort);
    const query = params.toString();
    return request<ConversationSummary[]>(
      `/api/conversations/${query ? `?${query}` : ""}`
    );
  },
  messages: (id: number) => request<Message[]>(`/api/conversations/${id}/messages`),
  delete: (id: number) =>
    request<{ detail: string }>(`/api/conversations/${id}`, { method: "DELETE" }),
};

// Admin
export interface Stats {
  total_users: number;
  total_conversations: number;
  total_messages: number;
  total_security_events: number;
  locked_users: number;
}

export interface AdminUser {
  id: number;
  email: string;
  full_name: string | null;
  role: string;
  is_active: boolean;
  failed_login_attempts: number;
  is_locked: boolean;
}

export interface SecurityEvent {
  id: number;
  event_type: string;
  email: string | null;
  user_id: number | null;
  status: string;
  ip_address: string | null;
  details: string | null;
  created_at: string;
  acknowledged: boolean;
}

export interface GuardrailPolicy {
  id: number;
  pattern: string;
  reason: string;
  is_active: boolean;
  created_at: string;
  acknowledged: boolean;
}

// Reference (Knowledge Base) ─ shapes match backend/data/*.py
export interface SeverityLevel {
  level: string;
  color: string;
  what_it_means: string;
  typical_indicators: string[];
  typical_scenarios: string[];
  why_dangerous: string;
  why_not_higher: string;
  why_not_lower: string;
  response_sla: string;
}

export interface Threat {
  id: string;
  name: string;
  stride_category: string;
  primary_agent: string;
  description: string;
  attack_example: string;
  detection_indicators: string[];
  mitigation: string;
}

export interface StrideScenario {
  attack: string;
  affected_component: string;
  risk: string;
  mitigation: string;
  residual_risk: string;
}

export interface StrideCategory {
  category: string;
  definition: string;
  scenarios: StrideScenario[];
}

export interface RiskMatrixRow {
  threat_id: string;
  threat: string;
  stride: string;
  likelihood: string;
  impact: string;
  severity: string;
  affected_component: string;
  mitigation: string;
  residual_risk: string;
  why_this_severity: string;
}

export interface MitreTechnique {
  id: string;
  name: string;
  tactic: string;
  description: string;
  detection_indicators: string[];
  mitigations: string[];
  mitre_url: string;
  // present when get_technique() resolved a sub-id to its parent:
  requested_id?: string;
  sub_technique?: boolean;
}

export const reference = {
  severity: () => request<SeverityLevel[]>("/api/reference/severity"),
  threats: () => request<Threat[]>("/api/reference/threats"),
  stride: () => request<StrideCategory[]>("/api/reference/stride"),
  riskMatrix: () => request<RiskMatrixRow[]>("/api/reference/risk-matrix"),
  mitre: () => request<MitreTechnique[]>("/api/reference/mitre"),
};

// Canonical attack.mitre.org URL for any ATT&CK ID (parent or sub-technique).
// Used by the autolinker and the "not in dictionary" fallback card.
export function mitreUrl(id: string): string {
  const canonical = id.trim().toUpperCase();
  if (canonical.includes(".")) {
    const [parent, sub] = canonical.split(".", 2);
    return `https://attack.mitre.org/techniques/${parent}/${sub}/`;
  }
  return `https://attack.mitre.org/techniques/${canonical}/`;
}

export const admin = {
  stats: () => request<Stats>("/api/admin/stats"),
  users: () => request<AdminUser[]>("/api/admin/users"),
  unlockUser: (id: number) =>
    request<{ detail: string; was_locked: boolean }>(`/api/admin/users/${id}/unlock`, {
      method: "POST",
    }),
  updateUserRole: (id: number, role: string) =>
    request<{ detail: string }>(`/api/admin/users/${id}/role`, {
      method: "PATCH",
      body: JSON.stringify({ role }),
    }),
  updateUserStatus: (id: number, is_active: boolean) =>
    request<{ detail: string }>(`/api/admin/users/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ is_active }),
    }),
  deleteUser: (id: number) =>
    request<{ detail: string }>(`/api/admin/users/${id}`, {
      method: "DELETE",
    }),
  securityEvents: (eventType?: string, limit = 100) => {
    const params = new URLSearchParams();
    if (eventType) params.set("event_type", eventType);
    params.set("limit", String(limit));
    return request<SecurityEvent[]>(`/api/admin/security-events?${params.toString()}`);
  },
      acknowledgeAllEvents: () =>
    request<{ detail: string }>(`/api/admin/security-events/acknowledge-all`, {
      method: "POST",
    }),
  acknowledgeEvent: (id: number) =>
    request<{ detail: string }>(`/api/admin/security-events/${id}/acknowledge`, {
      method: "POST",
    }),
  listPolicies: () => request<GuardrailPolicy[]>("/api/admin/guardrail-policies"),
  createPolicy: (pattern: string, reason: string) =>
    request<GuardrailPolicy>("/api/admin/guardrail-policies", {
      method: "POST",
      body: JSON.stringify({ pattern, reason }),
    }),
  deletePolicy: (id: number) =>
    request<{ detail: string }>(`/api/admin/guardrail-policies/${id}`, {
      method: "DELETE",
    }),
};
