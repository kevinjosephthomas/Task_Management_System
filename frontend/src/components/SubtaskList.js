import React, { useEffect, useState } from "react";
import {
  getSubtasks,
  createSubtask,
  updateSubtask,
  deleteSubtask,
  getSubtaskCompletion,
} from "../api";
import "../styles/SubtaskList.css";

export default function SubtaskList({ taskId, onClose }) {
  const [subtasks, setSubtasks] = useState([]);
  const [completion, setCompletion] = useState({ total: 0, completed: 0, percentage: 0 });
  const [newTitle, setNewTitle] = useState("");
  const [loading, setLoading] = useState(true);

  const load = async () => {
    try {
      const [subs, stats] = await Promise.all([
        getSubtasks(taskId),
        getSubtaskCompletion(taskId),
      ]);
      setSubtasks(subs || []);
      setCompletion(stats);
    } catch (e) {
      // silently fail
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (taskId) load();
  }, [taskId]);

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!newTitle.trim()) return;
    await createSubtask(taskId, { title: newTitle.trim() });
    setNewTitle("");
    load();
  };

  const handleToggle = async (sub) => {
    await updateSubtask(taskId, sub.id, { completed: !sub.completed });
    load();
  };

  const handleDelete = async (subId) => {
    await deleteSubtask(taskId, subId);
    load();
  };

  if (!taskId) return null;

  return (
    <div className="subtask-overlay" onClick={onClose}>
      <div className="subtask-panel" onClick={(e) => e.stopPropagation()}>
        <div className="subtask-panel-header">
          <h3>Checklist</h3>
          <button className="subtask-close" onClick={onClose} aria-label="Close">
            &times;
          </button>
        </div>

        <div className="subtask-progress">
          <div className="progress-bar-track">
            <div
              className="progress-bar-fill"
              style={{ width: `${completion.percentage}%` }}
            />
          </div>
          <span className="progress-text">
            {completion.completed}/{completion.total} items complete
            ({completion.percentage}%)
          </span>
        </div>

        {loading ? (
          <div className="subtask-loading">Loading...</div>
        ) : (
          <div className="subtask-items">
            {subtasks.map((sub) => (
              <div
                key={sub.id}
                className={`subtask-item${sub.completed ? " completed" : ""}`}
              >
                <input
                  type="checkbox"
                  checked={sub.completed}
                  onChange={() => handleToggle(sub)}
                  className="subtask-checkbox"
                />
                <span className="subtask-title">{sub.title}</span>
                <button
                  className="subtask-delete"
                  onClick={() => handleDelete(sub.id)}
                  aria-label={`Delete ${sub.title}`}
                >
                  &times;
                </button>
              </div>
            ))}
          </div>
        )}

        <form className="subtask-add-form" onSubmit={handleAdd}>
          <input
            type="text"
            placeholder="Add checklist item..."
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            maxLength={255}
          />
          <button type="submit" disabled={!newTitle.trim()}>
            Add
          </button>
        </form>
      </div>
    </div>
  );
}
