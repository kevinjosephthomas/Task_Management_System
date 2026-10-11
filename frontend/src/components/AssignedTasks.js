import React, { useEffect, useState } from "react";
import { getAssignedTasks, errorMessage } from "../api";
import DeadlineCountdown from "./DeadlineCountdown";

const PRIORITY_COLORS = { high: "#dc3545", medium: "#fd7e14", low: "#20c997" };

export default function AssignedTasks() {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const load = async () => {
      try {
        const data = await getAssignedTasks();
        setTasks(data.tasks || data || []);
      } catch (e) {
        setError(errorMessage(e));
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) return <div style={{ padding: "2rem", textAlign: "center", color: "#888" }}>Loading...</div>;

  return (
    <div style={{ padding: "1rem 1.25rem" }}>
      <h2 style={{ fontSize: "1rem", fontWeight: 700, marginBottom: "1rem", color: "#333" }}>
        Tasks Assigned to Me
      </h2>

      {error && (
        <div style={{ background: "#fdecea", color: "#b71c1c", padding: "0.75rem", borderRadius: 8, marginBottom: "1rem", fontSize: "0.9rem" }}>
          {error}
        </div>
      )}

      {tasks.length === 0 ? (
        <div style={{ textAlign: "center", color: "#888", padding: "2rem", fontSize: "0.9rem" }}>
          No tasks assigned to you yet.
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "0.65rem", maxWidth: 700 }}>
          {tasks.map((task) => (
            <div
              key={task.id}
              style={{
                background: "#fff",
                borderRadius: 10,
                padding: "0.9rem 1rem",
                boxShadow: "0 1px 4px rgba(0,0,0,0.08)",
                borderLeft: `3px solid ${PRIORITY_COLORS[task.priority] || "#aaa"}`,
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                <span style={{ fontSize: "0.75rem", color: "#bbb", fontWeight: 600 }}>#{task.id}</span>
                <span
                  style={{
                    fontSize: "0.65rem",
                    fontWeight: 700,
                    textTransform: "uppercase",
                    padding: "0.2rem 0.45rem",
                    borderRadius: 4,
                    color: "#fff",
                    background: PRIORITY_COLORS[task.priority] || "#aaa",
                  }}
                >
                  {task.priority}
                </span>
              </div>
              <div style={{ fontSize: "0.9rem", fontWeight: 600, color: "#222", marginBottom: 4 }}>{task.title}</div>
              {task.description && (
                <div style={{ fontSize: "0.8rem", color: "#777", marginBottom: 4 }}>{task.description}</div>
              )}
              <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                <span
                  style={{
                    fontSize: "0.72rem",
                    fontWeight: 600,
                    padding: "2px 8px",
                    borderRadius: 4,
                    background: task.status === "completed" ? "#e8f5e9" : task.status === "in-progress" ? "#fff3cd" : "#f4f5f7",
                    color: task.status === "completed" ? "#2e7d32" : task.status === "in-progress" ? "#856404" : "#6c757d",
                  }}
                >
                  {task.status}
                </span>
                {task.deadline_info && <DeadlineCountdown deadlineInfo={task.deadline_info} />}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
