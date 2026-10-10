import React, { useState, useCallback } from "react";
import KanbanBoard from "./KanbanBoard";
import TaskForm from "./TaskForm";
import Analytics from "./Analytics";
import "../styles/TaskList.css";

const VIEWS = [
  { id: "kanban",    label: "📊 Kanban" },
  { id: "analytics", label: "📈 Analytics" },
];

export default function TaskList() {
  const [view, setView] = useState("kanban");
  const [refreshKey, setRefreshKey] = useState(0);

  const handleTaskCreated = useCallback(() => {
    setRefreshKey((k) => k + 1);
  }, []);

  return (
    <div className="task-list-container">
      <div className="view-controls">
        {VIEWS.map(({ id, label }) => (
          <button
            key={id}
            id={`view-btn-${id}`}
            className={`view-btn${view === id ? " active" : ""}`}
            onClick={() => setView(id)}
          >
            {label}
          </button>
        ))}
      </div>

      {view !== "analytics" && <TaskForm onCreated={handleTaskCreated} />}

      {view === "kanban" && <KanbanBoard key={refreshKey} />}
      {view === "analytics" && <Analytics />}
    </div>
  );
}
