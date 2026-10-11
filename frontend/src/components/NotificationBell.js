import React, { useEffect, useState, useRef } from "react";
import { getOverdueTasks, getUpcomingTasks, getNotifications, markNotificationRead, markAllNotificationsRead } from "../api";
import "../styles/NotificationBell.css";

const PRIORITY_COLORS = { high: "#dc3545", medium: "#fd7e14", low: "#20c997" };

const NOTIF_ICONS = {
  task_assigned: "📩",
  collaborator_added: "👥",
  deadline_reminder: "⏰",
  overdue_alert: "⚠️",
};

export default function NotificationBell() {
  const [overdue, setOverdue] = useState([]);
  const [upcoming, setUpcoming] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [open, setOpen] = useState(false);
  const [tab, setTab] = useState("reminders");
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

  const loadNotifications = async () => {
    try {
      const data = await getNotifications(false, 30);
      setNotifications(data.notifications || []);
    } catch (e) {
      // silently fail
    }
  };

  useEffect(() => {
    loadReminders();
    loadNotifications();
    const timer = setInterval(() => {
      loadReminders();
      loadNotifications();
    }, 5 * 60 * 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    const handleClick = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const unreadCount = notifications.filter((n) => !n.read).length;
  const reminderCount = overdue.length + upcoming.length;
  const totalCount = unreadCount + reminderCount;

  const handleMarkRead = async (id) => {
    try {
      await markNotificationRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, read: true } : n))
      );
    } catch (e) {
      // silently fail
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await markAllNotificationsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
    } catch (e) {
      // silently fail
    }
  };

  return (
    <div className="notification-bell" ref={ref}>
      <button
        className="bell-btn"
        onClick={() => setOpen(!open)}
        aria-label="Notifications"
      >
        <span role="img" aria-label="bell">{"🔔"}</span>
        {totalCount > 0 && <span className="bell-badge">{totalCount}</span>}
      </button>

      {open && (
        <div className="bell-dropdown">
          <div className="bell-tabs">
            <button
              className={`bell-tab${tab === "reminders" ? " active" : ""}`}
              onClick={() => setTab("reminders")}
            >
              Reminders {reminderCount > 0 && `(${reminderCount})`}
            </button>
            <button
              className={`bell-tab${tab === "notifications" ? " active" : ""}`}
              onClick={() => setTab("notifications")}
            >
              Inbox {unreadCount > 0 && `(${unreadCount})`}
            </button>
          </div>

          {tab === "reminders" && (
            <>
              {reminderCount === 0 ? (
                <div className="bell-empty">No reminders</div>
              ) : (
                <>
                  {overdue.length > 0 && (
                    <div className="bell-section">
                      <div className="bell-section-title overdue-title">
                        {"⚠️"} Overdue
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
                        {"📅"} Due Soon
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
            </>
          )}

          {tab === "notifications" && (
            <>
              {notifications.length === 0 ? (
                <div className="bell-empty">No notifications</div>
              ) : (
                <>
                  {unreadCount > 0 && (
                    <button className="bell-mark-all" onClick={handleMarkAllRead}>
                      Mark all as read
                    </button>
                  )}
                  {notifications.map((n) => (
                    <div
                      key={n.id}
                      className={`bell-item notif-item${n.read ? "" : " unread"}`}
                      onClick={() => !n.read && handleMarkRead(n.id)}
                    >
                      <div className="bell-item-header">
                        <span className="notif-icon">
                          {NOTIF_ICONS[n.type] || "🔔"}
                        </span>
                        <span className="bell-item-title">{n.message}</span>
                      </div>
                      <div className="bell-item-meta">
                        {n.created_at ? new Date(n.created_at).toLocaleString() : ""}
                      </div>
                    </div>
                  ))}
                </>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
