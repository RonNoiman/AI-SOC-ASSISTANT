import { useState, useEffect, useCallback } from "react";
import type { FormEvent } from "react";
import {
  admin,
  type Stats,
  type AdminUser,
  type SecurityEvent,
  type GuardrailPolicy,
} from "../api/client";
import { useAuth } from "../context/AuthContext";
import { Navigate } from "react-router-dom";

type Tab = "users" | "events" | "routing" | "policies";

export default function Admin() {
  const { user } = useAuth();
  const [tab, setTab] = useState<Tab>("users");
  const [stats, setStats] = useState<Stats | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [routing, setRouting] = useState<SecurityEvent[]>([]);
  const [policies, setPolicies] = useState<GuardrailPolicy[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [newPattern, setNewPattern] = useState("");
  const [newReason, setNewReason] = useState("");

  const loadAll = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [s, u, e, r, p] = await Promise.all([
        admin.stats(),
        admin.users(),
        admin.securityEvents(undefined, 100),
        admin.securityEvents("routing_decision", 50),
        admin.listPolicies(),
      ]);
      setStats(s);
      setUsers(u);
      setEvents(e);
      setRouting(r);
      setPolicies(p);
    } catch (err: any) {
      setError(err.message || "Failed to load admin data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadAll();
  }, [loadAll]);

  if (user?.role !== "admin") {
    return <Navigate to="/chat" replace />;
  }

  const handleUnlock = async (u: AdminUser) => {
    if (!confirm(`Unlock ${u.email}?`)) return;
    try {
      await admin.unlockUser(u.id);
      await loadAll();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleRoleChange = async (u: AdminUser, newRole: string) => {
    if (!confirm(`Change role for ${u.email} to ${newRole}?`)) return;
    try {
      await admin.updateUserRole(u.id, newRole);
      await loadAll();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleStatusToggle = async (u: AdminUser) => {
    const action = u.is_active ? "deactivate" : "activate";
    if (!confirm(`Are you sure you want to ${action} ${u.email}?`)) return;
    try {
      await admin.updateUserStatus(u.id, !u.is_active);
      await loadAll();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleDeleteUser = async (u: AdminUser) => {
    if (
      !confirm(
        `WARNING: Are you absolutely sure you want to permanently delete ${u.email}? This cannot be undone and will delete all their conversation history.`,
      )
    )
      return;
    try {
      await admin.deleteUser(u.id);
      await loadAll();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleCreatePolicy = async (e: FormEvent) => {
    e.preventDefault();
    if (!newPattern.trim()) return;
    try {
      await admin.createPolicy(
        newPattern.trim(),
        newReason.trim() || "Custom admin policy",
      );
      setNewPattern("");
      setNewReason("");
      const p = await admin.listPolicies();
      setPolicies(p);
    } catch (err: any) {
      setError(err.message);
    }
  };

    const handleAcknowledgeAll = async () => {
    if (!confirm("Dismiss all active alerts?")) return;
    try {
      await admin.acknowledgeAllEvents();
      await loadAll();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleAcknowledge = async (id: number) => {
    try {
      await admin.acknowledgeEvent(id);
      await loadAll();
    } catch (err: any) {
      setError(err.message);
    }
  };

  const unacknowledgedAlerts = events.filter(
    (e) => e.event_type === "guardrail_block" && !e.acknowledged,
  );

  const handleDeletePolicy = async (id: number) => {
    if (!confirm("Delete this policy?")) return;
    try {
      await admin.deletePolicy(id);
      const p = await admin.listPolicies();
      setPolicies(p);
    } catch (err: any) {
      setError(err.message);
    }
  };

  if (loading)
    return (
      <p className="muted" style={{ padding: "2rem" }}>
        Loading...
      </p>
    );

  return (
    <div className="admin-page">
      <div className="admin-header">
        <h2>Admin Dashboard</h2>
        <button className="btn-secondary" onClick={() => void loadAll()}>
          Refresh
        </button>
      </div>

      {error && (
        <div className="error-msg" style={{ margin: "0 0 1rem" }}>
          {error}
        </div>
      )}

      
      {unacknowledgedAlerts.length > 0 && (
        <div style={{ backgroundColor: "#fee2e2", border: "1px solid #ef4444", padding: "1rem", borderRadius: "8px", marginBottom: "1.5rem", color: "#991b1b" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.5rem" }}>
            <h3 style={{ display: "flex", alignItems: "center", gap: "0.5rem", margin: 0, color: "#b91c1c" }}>
              <span style={{ fontSize: "1.2rem" }}>🚨</span> Active Security Alerts ({unacknowledgedAlerts.length})
            </h3>
            <button 
              onClick={handleAcknowledgeAll}
              style={{ padding: "0.4rem 0.8rem", background: "#b91c1c", color: "white", border: "none", borderRadius: "6px", fontSize: "0.85rem", cursor: "pointer", fontWeight: 600 }}
            >
              Dismiss All
            </button>
          </div>
          <p style={{ margin: 0, fontSize: "0.9rem" }}>Users have attempted restricted actions or triggered guardrails. Please review the Audit Log to dismiss them.</p>
        </div>
      )}
      <div className="stat-cards">

        <div className="stat-card">
          <div className="stat-value">{stats?.total_users}</div>
          <div className="stat-label">Total Users</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats?.total_conversations}</div>
          <div className="stat-label">Conversations</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats?.total_messages}</div>
          <div className="stat-label">Messages</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats?.total_security_events}</div>
          <div className="stat-label">Audit Events</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{stats?.locked_users}</div>
          <div className="stat-label">Locked Users</div>
        </div>
      </div>

      <div className="admin-tabs">
        <button
          className={`admin-tab ${tab === "users" ? "active" : ""}`}
          onClick={() => setTab("users")}
        >
          Users
        </button>
        <button
          className={`admin-tab ${tab === "events" ? "active" : ""}`}
          onClick={() => setTab("events")}
        >
          Audit Log
        </button>
        <button
          className={`admin-tab ${tab === "routing" ? "active" : ""}`}
          onClick={() => setTab("routing")}
        >
          Routing Decisions
        </button>
        <button
          className={`admin-tab ${tab === "policies" ? "active" : ""}`}
          onClick={() => setTab("policies")}
        >
          Guardrail Policies
        </button>
      </div>

      {tab === "users" && (
        <div className="admin-section">
          <h3>Registered Users</h3>
          <table className="admin-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Email</th>
                <th>Name</th>
                <th>Role</th>
                <th>Status</th>
                <th>Failed Logins</th>
                <th>Change Role</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id}>
                  <td>{u.id}</td>
                  <td>{u.email}</td>
                  <td>{u.full_name || "-"}</td>
                  <td>
                    <span className={`role-badge ${u.role}`}>{u.role}</span>
                  </td>
                  <td>
                    {u.is_locked ? (
                      <span
                        className="status-dot inactive"
                        style={{ marginRight: 6 }}
                      />
                    ) : (
                      <span
                        className={`status-dot ${u.is_active ? "active" : "inactive"}`}
                        style={{ marginRight: 6 }}
                      />
                    )}
                    {u.is_locked
                      ? "Locked"
                      : u.is_active
                        ? "Active"
                        : "Disabled"}
                  </td>
                  <td>{u.failed_login_attempts}</td>
                  <td>
                    <select
                      value={u.role}
                      onChange={(e) => handleRoleChange(u, e.target.value)}
                      disabled={u.id === user?.id}
                      style={{ padding: "0.25rem", borderRadius: "4px" }}
                    >
                      <option value="analyst">Analyst</option>
                      <option value="admin">Admin</option>
                    </select>
                  </td>
                  <td>
                    {u.is_locked && (
                      <button
                        className="btn-secondary"
                        onClick={() => handleUnlock(u)}
                        style={{ marginRight: "0.5rem" }}
                      >
                        Unlock
                      </button>
                    )}
                    <button
                      className="btn-secondary"
                      onClick={() => handleStatusToggle(u)}
                      disabled={u.id === user?.id}
                      style={{ marginRight: "0.5rem" }}
                    >
                      {u.is_active ? "Disable" : "Enable"}
                    </button>
                    <button
                      onClick={() => handleDeleteUser(u)}
                      disabled={u.id === user?.id}
                      style={{
                        backgroundColor: "transparent",
                        border: "1px solid #f87171",
                        color: "#ef4444",
                        padding: "0.2rem 0.5rem",
                        fontSize: "0.8rem",
                        borderRadius: "4px",
                        cursor: u.id === user?.id ? "not-allowed" : "pointer",
                        opacity: u.id === user?.id ? 0.5 : 1,
                      }}
                      onMouseOver={(e) => {
                        if (u.id !== user?.id) {
                          e.currentTarget.style.backgroundColor = "#fee2e2";
                          e.currentTarget.style.color = "#991b1b";
                        }
                      }}
                      onMouseOut={(e) => {
                        if (u.id !== user?.id) {
                          e.currentTarget.style.backgroundColor = "transparent";
                          e.currentTarget.style.color = "#ef4444";
                        }
                      }}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === "events" && (
        <div className="admin-section">
          <h3>Audit Log (most recent 100)</h3>
          <table className="admin-table">
            <thead>
              <tr>
                <th>When</th>
                <th>Event</th>
                <th>Status</th>
                <th>Email</th>
                <th>IP</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              {events.map((e) => (
                <tr key={e.id}>
                  <td>{new Date(e.created_at).toLocaleString()}</td>
                  <td>{e.event_type}</td>
                  <td>
                    <span className={`role-badge ${e.status}`}>{e.status}</span>
                  </td>
                  <td>{e.email || "-"}</td>
                  <td>{e.ip_address || "-"}</td>
                  <td className="audit-details">
                    <div>{e.details || "-"}</div>
                    {e.event_type === "guardrail_block" && !e.acknowledged && (
                      <button
                        onClick={() => handleAcknowledge(e.id)}
                        style={{
                          marginTop: "0.5rem",
                          padding: "0.2rem 0.5rem",
                          background: "#ef4444",
                          color: "white",
                          border: "none",
                          borderRadius: "4px",
                          fontSize: "0.75rem",
                          cursor: "pointer",
                        }}
                      >
                        Dismiss Alert
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {tab === "routing" && (
        <div className="admin-section">
          <h3>Routing Decisions (most recent 50)</h3>
          <table className="admin-table">
            <thead>
              <tr>
                <th>When</th>
                <th>Email</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              {routing.map((e) => (
                <tr key={e.id}>
                  <td>{new Date(e.created_at).toLocaleString()}</td>
                  <td>{e.email || "-"}</td>
                  <td className="audit-details">
                    <div>{e.details || "-"}</div>
                    {e.event_type === "guardrail_block" && !e.acknowledged && (
                      <button
                        onClick={() => handleAcknowledge(e.id)}
                        style={{
                          marginTop: "0.5rem",
                          padding: "0.2rem 0.5rem",
                          background: "#ef4444",
                          color: "white",
                          border: "none",
                          borderRadius: "4px",
                          fontSize: "0.75rem",
                          cursor: "pointer",
                        }}
                      >
                        Dismiss Alert
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {routing.length === 0 && (
            <p className="muted">No routing decisions recorded yet.</p>
          )}
        </div>
      )}

      {tab === "policies" && (
        <div className="admin-section">
          <h3>Custom Guardrail Policies</h3>
          <p className="muted" style={{ marginBottom: "1rem" }}>
            These regex patterns are checked on top of the built-in guardrails.
            Any user message that matches will be blocked.
          </p>
          <form onSubmit={handleCreatePolicy} className="policy-form">
            <input
              type="text"
              value={newPattern}
              onChange={(e) => setNewPattern(e.target.value)}
              placeholder="Regex pattern, e.g. (?i)secret\s+plan"
              required
            />
            <input
              type="text"
              value={newReason}
              onChange={(e) => setNewReason(e.target.value)}
              placeholder="Reason (optional)"
            />
            <button type="submit" className="btn-primary">
              Add policy
            </button>
          </form>
          <table className="admin-table" style={{ marginTop: "1rem" }}>
            <thead>
              <tr>
                <th>ID</th>
                <th>Pattern</th>
                <th>Reason</th>
                <th>Created</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {policies.map((p) => (
                <tr key={p.id}>
                  <td>{p.id}</td>
                  <td>
                    <code>{p.pattern}</code>
                  </td>
                  <td>{p.reason}</td>
                  <td>{new Date(p.created_at).toLocaleString()}</td>
                  <td>
                    <button
                      className="btn-secondary"
                      onClick={() => handleDeletePolicy(p.id)}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {policies.length === 0 && (
            <p className="muted">
              No custom policies yet — only built-in guardrails are active.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
