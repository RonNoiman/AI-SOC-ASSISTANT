import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useEffect, useState } from "react";

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [theme, setTheme] = useState<"light" | "dark">(
    (localStorage.getItem("theme") as "light" | "dark") || "dark"
  );

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => prev === "dark" ? "light" : "dark");
  };


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
          <button 
            onClick={toggleTheme} 
            style={{ 
              width: "100%", 
              marginBottom: "1rem", 
              padding: "0.4rem", 
              background: "transparent", 
              border: "1px solid var(--border)", 
              borderRadius: "4px", 
              color: "var(--text-secondary)", 
              cursor: "pointer" 
            }}
          >
            {theme === "dark" ? "☀️ Light Mode" : "🌙 Dark Mode"}
          </button>
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
