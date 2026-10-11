import React, { useEffect, useState } from "react";
import { getTaskActivity } from "../api";
import "../styles/TaskActivityTimeline.css";

const ACTION_ICONS = {
  created: "✨",
  updated: "✏️",
  status_changed: "🔄",
  deleted: "🗑️",
};

export default function TaskActivityTimeline({ taskId, onClose }) {
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!taskId) return;
    setLoading(true);
    getTaskActivity(taskId)
      .then((data) => setActivities(data.activities || []))
      .catch(() => setActivities([]))
      .finally(() => setLoading(false));
  }, [taskId]);

  if (!taskId) return null;

  return (
    <div className="activity-overlay" onClick={onClose}>
      <div className="activity-panel" onClick={(e) => e.stopPropagation()}>
        <div className="activity-panel-header">
          <h3>Activity History</h3>
          <button className="activity-close" onClick={onClose} aria-label="Close">
            &times;
          </button>
        </div>

        {loading ? (
          <div className="activity-loading">Loading...</div>
        ) : activities.length === 0 ? (
          <div className="activity-empty">No activity recorded</div>
        ) : (
          <div className="activity-timeline">
            {activities.map((a) => (
              <div key={a.id} className={`timeline-item action-${a.action}`}>
                <div className="timeline-dot">
                  {ACTION_ICONS[a.action] || "•"}
                </div>
                <div className="timeline-content">
                  <div className="timeline-action">
                    <strong>{a.action.replace("_", " ")}</strong>
                    {a.field_name && (
                      <span className="timeline-field"> &mdash; {a.field_name}</span>
                    )}
                  </div>
                  {a.old_value && a.new_value && (
                    <div className="timeline-change">
                      <span className="old-value">{a.old_value}</span>
                      <span className="change-arrow">&rarr;</span>
                      <span className="new-value">{a.new_value}</span>
                    </div>
                  )}
                  {!a.old_value && a.new_value && (
                    <div className="timeline-change">
                      <span className="new-value">{a.new_value}</span>
                    </div>
                  )}
                  <div className="timeline-meta">
                    {a.user_email && <span className="timeline-user">{a.user_email}</span>}
                    {a.created_at && (
                      <span className="timeline-time">
                        {new Date(a.created_at).toLocaleString()}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
