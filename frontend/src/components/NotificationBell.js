import React, { useEffect, useState, useRef } from "react";
import { getOverdueTasks, getUpcomingTasks } from "../api";
import "../styles/NotificationBell.css";

const PRIORITY_COLORS = { high: "#dc3545", medium: "#fd7e14", low: "#20c997" };

export default function NotificationBell() {
  const [overdue, setOverdue] = useState([]);
  const [upcoming, setUpcoming] = useState([]);
  const [open, setOpen] = useState(false);
  const ref = useRef(null);

  const loadReminders = async () => {
    try {
      const [od, up] = await Promise.all([getOverdueTasks(), getUpcomingTasks(3)]);
      setOverdue(od.tasks || []);
      setUpcoming(up.tasks || []);
    } catch (e) {
      // silently fail
    }
  };

  useEffect(() => {
    loadReminders();
    const timer = setInterval(loadReminders, 5 * 60 * 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    const handleClick = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const totalCount = overdue.length + upcoming.length;

  return (
    <div className="notification-bell" ref={ref}>
      <button
        className="bell-btn"
        onClick={() => setOpen(!open)}
        aria-label="Notifications"
      >
        <span role="img" aria-label="bell">&#x1F514;</span>
        {totalCount > 0 && <span className="bell-badge">{totalCount}</span>}
      </button>

      {open && (
        <div className="bell-dropdown">
          {totalCount === 0 ? (
            <div className="bell-empty">No reminders</div>
          ) : (
            <>
              {overdue.length > 0 && (
                <div className="bell-section">
                  <div className="bell-section-title overdue-title">
                    <span role="img" aria-label="warning">&#x26A0;&#xFE0F;</span> Overdue
                  </div>
                  {overdue.map((t) => (
                    <div key={t.id} className="bell-item overdue-item">
                      <div className="bell-item-header">
                        <span className="bell-item-title">{t.title}</span>
                        <span
                          className="bell-priority"
                          style={{ background: PRIORITY_COLORS[t.priority] }}
                        >
                          {t.priority}
                        </span>
                      </div>
                      <div className="bell-item-meta">
                        {t.days_overdue} day{t.days_overdue !== 1 ? "s" : ""} ago
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {upcoming.length > 0 && (
                <div className="bell-section">
                  <div className="bell-section-title upcoming-title">
                    <span role="img" aria-label="calendar">&#x1F4C5;</span> Due Soon
                  </div>
                  {upcoming.map((t) => (
                    <div key={t.id} className="bell-item upcoming-item">
                      <div className="bell-item-header">
                        <span className="bell-item-title">{t.title}</span>
                        <span
                          className="bell-priority"
                          style={{ background: PRIORITY_COLORS[t.priority] }}
                        >
                          {t.priority}
                        </span>
                      </div>
                      <div className="bell-item-meta">
                        {t.days_until_due === 0
                          ? "Due today"
                          : `in ${t.days_until_due} day${t.days_until_due !== 1 ? "s" : ""}`}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
