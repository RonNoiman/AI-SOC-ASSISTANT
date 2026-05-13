import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `nav-link ${isActive ? "active" : ""}`;

  return (
    <div className="app-layout">
      <nav className="sidebar">
        <div className="sidebar-header">
          <div className="logo">
            <span className="logo-icon">&#9737;</span>
            <span>SOC Assistant</span>
          </div>
          <p className="sidebar-subtitle">
            Multi-agent guidance for network, identity, and policy questions.
          </p>
        </div>

        <div className="nav-links">
          <NavLink to="/chat" className={linkClass}>
            <span className="nav-icon">&#9655;</span> Chat
          </NavLink>
          <NavLink to="/history" className={linkClass}>
            <span className="nav-icon">&#8986;</span> History
          </NavLink>
          {user?.role === "admin" && (
            <NavLink to="/admin" className={linkClass}>
              <span className="nav-icon">&#9881;</span> Admin
            </NavLink>
          )}
        </div>

        <div className="sidebar-footer">
          <div className="user-info">
            <div className="user-name">{user?.full_name || user?.email}</div>
            <div className="user-role">{user?.role}</div>
          </div>
          <button className="btn-logout" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </nav>

      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
