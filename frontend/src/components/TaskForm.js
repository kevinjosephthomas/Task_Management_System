import React, { useState } from "react";
import { createTask, errorMessage } from "../api";
import "../styles/TaskForm.css";

export default function TaskForm({ onCreated }) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState("medium");
  const [dueDate, setDueDate] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await createTask({
        title,
        description: description || null,
        priority,
        due_date: dueDate || null,
      });
      setTitle("");
      setDescription("");
      setPriority("medium");
      setDueDate("");
      setOpen(false);
      if (onCreated) onCreated();
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="task-form-wrapper">
      {!open ? (
        <button id="open-task-form" className="open-form-btn" onClick={() => setOpen(true)}>
          + New Task
        </button>
      ) : (
        <div className="task-form-card">
          <div className="task-form-header">
            <h3>New Task</h3>
            <button className="close-form-btn" onClick={() => setOpen(false)} aria-label="Close">×</button>
          </div>

          {error && (
            <div className="form-error" role="alert">
              {error}
              <button onClick={() => setError("")}>×</button>
            </div>
          )}

          <form onSubmit={handleSubmit} className="task-form">
            <input
              id="task-title"
              type="text"
              placeholder="Task title *"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              maxLength={200}
              autoFocus
            />
            <textarea
              id="task-description"
              placeholder="Description (optional)"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
            />
            <div className="form-row">
              <select
                id="task-priority"
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
              >
                <option value="low">🟢 Low Priority</option>
                <option value="medium">🟠 Medium Priority</option>
                <option value="high">🔴 High Priority</option>
              </select>
              <input
                id="task-due-date"
                type="date"
                value={dueDate}
                onChange={(e) => setDueDate(e.target.value)}
                title="Due date (optional)"
              />
            </div>
            <div className="form-actions">
              <button type="button" className="cancel-btn" onClick={() => setOpen(false)}>
                Cancel
              </button>
              <button id="submit-task" type="submit" className="submit-btn" disabled={loading}>
                {loading ? "Adding…" : "Add Task"}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
