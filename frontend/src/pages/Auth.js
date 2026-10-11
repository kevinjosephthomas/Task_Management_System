import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import "../styles/Auth.css";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";
const GOOGLE_CLIENT_ID = process.env.REACT_APP_GOOGLE_CLIENT_ID || "";

export default function Auth({ onLogin }) {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [username, setUsername] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  const handleGoogleResponse = useCallback(async (response) => {
    setError("");
    setLoading(true);
    try {
      const res = await axios.post(`${API_URL}/auth/google`, { token: response.credential });
      localStorage.setItem("access_token", res.data.access_token);
      localStorage.setItem("user_email", "google-user");
      onLogin("google-user");
    } catch (err) {
      const detail = err.response?.data?.detail || "Google sign-in failed. Try again.";
      setError(typeof detail === "string" ? detail : JSON.stringify(detail));
    } finally {
      setLoading(false);
    }
  }, [onLogin]);

  useEffect(() => {
    if (!GOOGLE_CLIENT_ID) return;
    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    script.onload = () => {
      if (window.google) {
        window.google.accounts.id.initialize({
          client_id: GOOGLE_CLIENT_ID,
          callback: handleGoogleResponse,
        });
        window.google.accounts.id.renderButton(
          document.getElementById("google-signin-btn"),
          { theme: "outline", size: "large", width: "100%", text: "signin_with" }
        );
      }
    };
    document.body.appendChild(script);
    return () => { document.body.removeChild(script); };
  }, [handleGoogleResponse]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);

    try {
      const endpoint = mode === "login" ? "/auth/login" : "/auth/register";
      const payload = mode === "login"
        ? { email, password }
        : { email, password, username, full_name: fullName || undefined };
      const response = await axios.post(`${API_URL}${endpoint}`, payload);

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
        <div className="auth-logo">{"✅"}</div>
        <h1>{mode === "login" ? "Welcome back" : "Create account"}</h1>
        <p className="auth-subtitle">
          {mode === "login" ? "Sign in to manage your tasks" : "Start organising your work today"}
        </p>

        {error && <div className="auth-alert auth-alert--error" role="alert">{error}</div>}
        {success && <div className="auth-alert auth-alert--success" role="status">{success}</div>}

        {GOOGLE_CLIENT_ID && (
          <>
            <div id="google-signin-btn" className="google-btn-wrapper"></div>
            <div className="auth-divider">
              <span>or</span>
            </div>
          </>
        )}

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

          {mode === "register" && (
            <>
              <label className="auth-label">
                Username
                <input
                  id="auth-username"
                  type="text"
                  placeholder="cooluser"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  minLength={3}
                  autoComplete="username"
                />
              </label>
              <label className="auth-label">
                Full Name (optional)
                <input
                  id="auth-fullname"
                  type="text"
                  placeholder="Your Name"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  autoComplete="name"
                />
              </label>
            </>
          )}

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
