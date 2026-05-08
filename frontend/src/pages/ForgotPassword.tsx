import { useState } from "react";
import type { FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { auth } from "../api/client";

export default function ForgotPassword() {
  const [email, setEmail] = useState("");
  const [token, setToken] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loadingRequest, setLoadingRequest] = useState(false);
  const [loadingReset, setLoadingReset] = useState(false);
  const navigate = useNavigate();

  const handleRequest = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setLoadingRequest(true);
    try {
      const res = await auth.requestPasswordReset(email);
      setSuccess(`${res.detail} For local development, check the backend terminal for the token.`);
    } catch (err: any) {
      setError(err.message || "Could not request reset token");
    } finally {
      setLoadingRequest(false);
    }
  };

  const handleReset = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (newPassword !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    setLoadingReset(true);
    try {
      const res = await auth.confirmPasswordReset(token, newPassword);
      setSuccess(res.detail);
      setTimeout(() => navigate("/login"), 1200);
    } catch (err: any) {
      setError(err.message || "Password reset failed");
    } finally {
      setLoadingReset(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card auth-card-wide">
        <div className="auth-header">
          <span className="auth-logo">&#9737;</span>
          <h1>Reset Password</h1>
          <p>Request a one-time token, then use it to set a new password</p>
        </div>

        {error && <div className="error-msg">{error}</div>}
        {success && <div className="success-msg">{success}</div>}

        <form onSubmit={handleRequest}>
          <div className="form-group">
            <label>Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="analyst@company.com"
              required
            />
          </div>

          <button type="submit" className="btn-primary" disabled={loadingRequest}>
            {loadingRequest ? "Requesting token..." : "Request Reset Token"}
          </button>
        </form>

        <div className="auth-divider">Reset with token</div>

        <form onSubmit={handleReset}>
          <div className="form-group">
            <label>Reset Token</label>
            <input
              type="text"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder="Paste the one-time token"
              required
            />
          </div>

          <div className="form-group">
            <label>New Password</label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="Create a new password"
              minLength={6}
              required
            />
          </div>

          <div className="form-group">
            <label>Confirm Password</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Repeat the new password"
              minLength={6}
              required
            />
          </div>

          <button type="submit" className="btn-primary" disabled={loadingReset}>
            {loadingReset ? "Updating password..." : "Reset Password"}
          </button>
        </form>

        <p className="auth-footer">
          Remembered it? <Link to="/login">Back to Sign In</Link>
        </p>
      </div>
    </div>
  );
}
