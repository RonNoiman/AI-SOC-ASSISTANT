import { useState, useEffect } from "react";
import { admin, type Stats, type AdminUser, type SecurityEvent } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { Navigate } from "react-router-dom";

export default function Admin() {
  const { user } = useAuth();
  const [stats, setStats] = useState<Stats | null>(null);
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [events, setEvents] = useState<SecurityEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([admin.stats(), admin.users(), admin.securityEvents()])
      .then(([s, u, e]) => {
        setStats(s);
        setUsers(u);
        setEvents(e);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (user?.role !== "admin") {
    return <Navigate to="/chat" replace />;
  }

  if (loading) return <p className="muted" style={{ padding: "2rem" }}>Loading...</p>;
  if (error) return <div className="error-msg" style={{ margin: "2rem" }}>{error}</div>;

  return (
    <div className="admin-page">
      <h2>Admin Dashboard</h2>

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
      </div>

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
                  <span className={`status-dot ${u.is_active ? "active" : "inactive"}`} />
                  {u.is_active ? "Active" : "Inactive"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="admin-section">
        <h3>Recent Security Events</h3>
        {events.length === 0 ? (
          <div className="panel-note">
            <strong>No security events recorded yet.</strong>
            <span>Login attempts, password resets, and lockouts will appear here.</span>
          </div>
        ) : (
          <table className="admin-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Event</th>
                <th>Status</th>
                <th>Email</th>
                <th>IP</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              {events.map((event) => (
                <tr key={event.id}>
                  <td>{new Date(event.created_at).toLocaleString()}</td>
                  <td>{event.event_type}</td>
                  <td>
                    <span className={`event-badge ${event.status}`}>{event.status}</span>
                  </td>
                  <td>{event.email || "-"}</td>
                  <td>{event.ip_address || "-"}</td>
                  <td>{event.details || "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
