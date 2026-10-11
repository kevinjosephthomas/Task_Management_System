import React, { useEffect, useState } from "react";
import { getTasks, searchTasks, updateTask, deleteTask, errorMessage } from "../api";
import TaskActivityTimeline from "./TaskActivityTimeline";
import SubtaskList from "./SubtaskList";
import "../styles/KanbanBoard.css";

const COLUMNS = [
  { status: "pending",     label: "Pending",     color: "#6c757d" },
  { status: "in-progress", label: "In Progress",  color: "#f0a500" },
  { status: "completed",   label: "Completed",    color: "#28a745" },
];

const PRIORITY_COLORS = { high: "#dc3545", medium: "#fd7e14", low: "#20c997" };

export default function KanbanBoard({ onTaskChanged, searchParams }) {
  const [tasks, setTasks] = useState({ pending: [], "in-progress": [], completed: [] });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [draggedTask, setDraggedTask] = useState(null);
  const [dragOver, setDragOver] = useState(null);
  const [resultCount, setResultCount] = useState(null);
  const [activityTaskId, setActivityTaskId] = useState(null);
  const [subtaskTaskId, setSubtaskTaskId] = useState(null);

  const loadTasks = async () => {
    try {
      let all;
      if (searchParams && Object.keys(searchParams).length > 0) {
        const result = await searchTasks(searchParams);
        all = result.tasks;
        setResultCount(result.total);
      } else {
        all = await getTasks();
        setResultCount(null);
      }
      const byStatus = { pending: [], "in-progress": [], completed: [] };
      all.forEach((t) => { if (byStatus[t.status]) byStatus[t.status].push(t); });
      setTasks(byStatus);
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTasks();
    const timer = setInterval(loadTasks, 5000);
    return () => clearInterval(timer);
  }, [searchParams]);

  useEffect(() => { if (onTaskChanged) loadTasks(); }, [onTaskChanged]);

  const handleStatusChange = async (taskId, newStatus) => {
    setError("");
    try {
      await updateTask(taskId, { status: newStatus });
      await loadTasks();
    } catch (e) {
      setError(errorMessage(e));
      loadTasks();
    }
  };

  const handleDelete = async (taskId) => {
    setError("");
    try {
      await deleteTask(taskId);
      await loadTasks();
    } catch (e) {
      setError(errorMessage(e));
    }
  };

  const handleDrop = (newStatus) => {
    if (draggedTask && draggedTask.status !== newStatus) {
      handleStatusChange(draggedTask.id, newStatus);
    }
    setDraggedTask(null);
    setDragOver(null);
  };

  if (loading) return <div className="kanban-loading"><span className="spinner" />Loading tasks...</div>;

  const totalTasks = Object.values(tasks).reduce((sum, arr) => sum + arr.length, 0);

  return (
    <div className="kanban-container">
      {error && (
        <div className="kanban-error" role="alert">
          {error}
          <button onClick={() => setError("")} aria-label="dismiss">&times;</button>
        </div>
      )}

      {resultCount !== null && (
        <div className="kanban-result-count">
          Showing {totalTasks} of {resultCount} results
        </div>
      )}

      <div className="kanban-board">
        {COLUMNS.map(({ status, label, color }) => (
          <div
            key={status}
            className={`kanban-column ${dragOver === status ? "drag-over" : ""}`}
            onDragOver={(e) => { e.preventDefault(); setDragOver(status); }}
            onDragLeave={() => setDragOver(null)}
            onDrop={() => handleDrop(status)}
          >
            <div className="column-header" style={{ borderTopColor: color }}>
              <h2 style={{ color }}>{label}</h2>
              <span className="task-count" style={{ background: color }}>
                {tasks[status]?.length || 0}
              </span>
            </div>

            <div className="column-content">
              {(tasks[status] || []).map((task) => {
                const isOverdue = task.is_overdue;
                const isDragging = draggedTask?.id === task.id;
                const hasSubtasks = task.subtask_completion && task.subtask_completion.total > 0;
                return (
                  <div
                    key={task.id}
                    id={`task-card-${task.id}`}
                    className={`task-card${isDragging ? " dragging" : ""}${isOverdue ? " overdue" : ""}`}
                    draggable
                    onDragStart={() => setDraggedTask(task)}
                    onDragEnd={() => { setDraggedTask(null); setDragOver(null); }}
                  >
                    <div className="task-card-header">
                      <span className="task-id">#{task.id}</span>
                      <span
                        className="priority-badge"
                        style={{ background: PRIORITY_COLORS[task.priority] || "#aaa" }}
                      >
                        {task.priority}
                      </span>
                    </div>

                    <h3 className="task-title">{task.title}</h3>
                    {task.description && (
                      <p className="task-description">{task.description}</p>
                    )}

                    {task.due_date && (
                      <div className={`task-due${isOverdue ? " overdue-label" : ""}`}>
                        {new Date(task.due_date + "T00:00").toLocaleDateString()}
                        {isOverdue && " — Overdue!"}
                      </div>
                    )}

                    {hasSubtasks && (
                      <div className="task-subtask-progress">
                        <div className="mini-progress-track">
                          <div
                            className="mini-progress-fill"
                            style={{ width: `${task.subtask_completion.percentage}%` }}
                          />
                        </div>
                        <span className="mini-progress-text">
                          {task.subtask_completion.completed}/{task.subtask_completion.total}
                        </span>
                      </div>
                    )}

                    <div className="task-card-footer">
                      <select
                        className="status-select"
                        value={task.status}
                        onChange={(e) => handleStatusChange(task.id, e.target.value)}
                        aria-label={`Change status of ${task.title}`}
                      >
                        {COLUMNS.map(({ status: s, label: l }) => (
                          <option key={s} value={s}>{l}</option>
                        ))}
                      </select>
                      <div className="task-card-actions">
                        <button
                          className="action-btn"
                          onClick={() => setSubtaskTaskId(task.id)}
                          title="Checklist"
                        >
                          &#x2611;
                        </button>
                        <button
                          className="action-btn"
                          onClick={() => setActivityTaskId(task.id)}
                          title="Activity"
                        >
                          &#x1F4CB;
                        </button>
                        <button
                          className="delete-btn"
                          onClick={() => handleDelete(task.id)}
                          aria-label={`Delete ${task.title}`}
                          title="Delete task"
                        >
                          &#x1F5D1;
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
              {(!tasks[status] || tasks[status].length === 0) && (
                <div className="empty-column">
                  Drop tasks here
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {activityTaskId && (
        <TaskActivityTimeline
          taskId={activityTaskId}
          onClose={() => setActivityTaskId(null)}
        />
      )}

      {subtaskTaskId && (
        <SubtaskList
          taskId={subtaskTaskId}
          onClose={() => { setSubtaskTaskId(null); loadTasks(); }}
        />
      )}
    </div>
  );
}
