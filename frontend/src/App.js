import React, { useEffect, useState } from "react";
import Auth from "./pages/Auth";
import TaskList from "./components/TaskList";
import "./App.css";

export default function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [userEmail, setUserEmail] = useState("");

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    const email = localStorage.getItem("user_email");
    if (token && email) {
      setIsLoggedIn(true);
      setUserEmail(email);
    }
  }, []);

  const handleLogin = (email) => {
    setIsLoggedIn(true);
    setUserEmail(email || localStorage.getItem("user_email") || "");
  };

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user_email");
    setIsLoggedIn(false);
    setUserEmail("");
  };

  if (!isLoggedIn) {
    return <Auth onLogin={handleLogin} />;
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-header-brand">
          <span className="app-logo">✅</span>
          <h1>Task Manager</h1>
        </div>
        <div className="app-header-user">
          <span className="user-email" title={userEmail}>{userEmail}</span>
          <button id="logout-btn" className="logout-btn" onClick={handleLogout}>
            Log Out
          </button>
        </div>
      </header>
      <main>
        <TaskList />
      </main>
    </div>
  );
}
