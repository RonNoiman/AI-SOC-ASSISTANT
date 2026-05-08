const API_BASE = "http://localhost:8000";

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
    throw new Error(body.detail || `Request failed: ${res.status}`);
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
export const chat = {
  send: (message: string, conversation_id?: number) =>
    request<{ response: string; agent: string; conversation_id: number }>("/api/chat/", {
      method: "POST",
      body: JSON.stringify({ message, conversation_id }),
    }),
};

// Conversations
export interface ConversationSummary {
  id: number;
  title: string;
  created_at: string;
  message_count: number;
}

export interface Message {
  id: number;
  role: string;
  content: string;
  agent_used: string | null;
  created_at: string;
}

export const conversations = {
  list: () => request<ConversationSummary[]>("/api/conversations/"),
  messages: (id: number) => request<Message[]>(`/api/conversations/${id}/messages`),
  delete: (id: number) =>
    request<{ detail: string }>(`/api/conversations/${id}`, { method: "DELETE" }),
};

// Admin
export interface Stats {
  total_users: number;
  total_conversations: number;
  total_messages: number;
}

export interface AdminUser {
  id: number;
  email: string;
  full_name: string | null;
  role: string;
  is_active: boolean;
}

export const admin = {
  stats: () => request<Stats>("/api/admin/stats"),
  users: () => request<AdminUser[]>("/api/admin/users"),
};
