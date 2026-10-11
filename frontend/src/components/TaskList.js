import React, { useState, useCallback } from "react";
import KanbanBoard from "./KanbanBoard";
import TaskForm from "./TaskForm";
import Analytics from "./Analytics";
import SearchBar from "./SearchBar";
import AssignedTasks from "./AssignedTasks";
import "../styles/TaskList.css";

const VIEWS = [
  { id: "kanban",    label: "Kanban" },
  { id: "assigned",  label: "Assigned to Me" },
  { id: "analytics", label: "Analytics" },
];

export default function TaskList() {
  const [view, setView] = useState("kanban");
  const [refreshKey, setRefreshKey] = useState(0);
  const [searchParams, setSearchParams] = useState({});

  const handleTaskCreated = useCallback(() => {
    setRefreshKey((k) => k + 1);
  }, []);

  const handleSearch = useCallback((params) => {
    setSearchParams(params);
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

      {view !== "analytics" && view !== "assigned" && <TaskForm onCreated={handleTaskCreated} />}
      {view === "kanban" && <SearchBar onSearch={handleSearch} />}

      {view === "kanban" && (
        <KanbanBoard
          key={refreshKey}
          searchParams={searchParams}
        />
      )}
      {view === "assigned" && <AssignedTasks />}
      {view === "analytics" && <Analytics />}
    </div>
  );
}
