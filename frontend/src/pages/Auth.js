import React, { useState } from "react";
import axios from "axios";
import "../styles/Auth.css";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

export default function Auth({ onLogin }) {
  const [mode, setMode] = useState("login"); // "login" or "register"
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);

    try {
      const endpoint = mode === "login" ? "/auth/login" : "/auth/register";
      const response = await axios.post(`${API_URL}${endpoint}`, { email, password });

      if (mode === "register") {
        setSuccess("Account created! Please log in.");
        setMode("login");
        setPassword("");
      } else {
        localStorage.setItem("access_token", response.data.access_token);
        localStorage.setItem("user_email", email);
        onLogin(email);
      }
    } catch (err) {
      const detail = err.response?.data?.detail || "An error occurred. Try again.";
      setError(typeof detail === "string" ? detail : JSON.stringify(detail));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <div className="auth-logo">✅</div>
        <h1>{mode === "login" ? "Welcome back" : "Create account"}</h1>
        <p className="auth-subtitle">
          {mode === "login" ? "Sign in to manage your tasks" : "Start organising your work today"}
        </p>

        {error && <div className="auth-alert auth-alert--error" role="alert">{error}</div>}
        {success && <div className="auth-alert auth-alert--success" role="status">{success}</div>}

        <form onSubmit={handleSubmit} className="auth-form">
          <label className="auth-label">
            Email
            <input
              id="auth-email"
              type="email"
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
          </label>
          <label className="auth-label">
            Password
            <input
              id="auth-password"
              type="password"
              placeholder={mode === "register" ? "Min 6 characters" : "Your password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
              autoComplete={mode === "login" ? "current-password" : "new-password"}
            />
          </label>
          <button id="auth-submit" type="submit" className="auth-btn" disabled={loading}>
            {loading ? "Please wait…" : mode === "login" ? "Log In" : "Sign Up"}
          </button>
        </form>

        <p className="auth-toggle">
          {mode === "login" ? "Don't have an account?" : "Already have an account?"}
          {" "}
          <button
            type="button"
            onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(""); setSuccess(""); }}
          >
            {mode === "login" ? "Sign Up" : "Log In"}
          </button>
        </p>
      </div>
    </div>
  );
}
