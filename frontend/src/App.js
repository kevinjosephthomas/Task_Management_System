import React, { useCallback, useEffect, useState } from "react";
import { createTask, deleteTask, errorMessage, getTasks, updateTask } from "./api";

const STATUSES = ["pending", "in-progress", "completed"];
const POLL_MS = 5000; // simple real-time updates via polling

export default function App() {
  const [tasks, setTasks] = useState([]);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      setTasks(await getTasks());
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const timer = setInterval(load, POLL_MS);
    return () => clearInterval(timer);
  }, [load]);

  const run = async (fn) => {
    setError("");
    try {
      await fn();
      await load();
    } catch (e) {
      setError(errorMessage(e));
      load(); // resync so the UI reflects the real status
    }
  };

  const onAdd = (e) => {
    e.preventDefault();
    run(async () => {
      await createTask({ title, description: description || null });
      setTitle("");
      setDescription("");
    });
  };

  const counts = STATUSES.map((s) => ({ s, n: tasks.filter((t) => t.status === s).length }));

  return (
    <div className="container">
      <h1>Task Manager</h1>

      {error && (
        <div className="error" role="alert">
          {error}
          <button onClick={() => setError("")} aria-label="dismiss">×</button>
        </div>
      )}

      <form onSubmit={onAdd} className="add-form">
        <input
          placeholder="Title *"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
          maxLength={200}
        />
        <input
          placeholder="Description"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
        <button type="submit">Add task</button>
      </form>

      <div className="summary">
        {counts.map(({ s, n }) => (
          <span key={s} className={`badge ${s}`}>{s}: {n}</span>
        ))}
      </div>

      {loading ? (
        <p>Loading…</p>
      ) : tasks.length === 0 ? (
        <p>No tasks yet.</p>
      ) : (
        <table>
          <thead>
            <tr><th>ID</th><th>Title</th><th>Description</th><th>Status</th><th>Created</th><th></th></tr>
          </thead>
          <tbody>
            {tasks.map((t) => (
              <tr key={t.id}>
                <td>{t.id}</td>
                <td>{t.title}</td>
                <td>{t.description}</td>
                <td>
                  <select
                    value={t.status}
                    className={`badge ${t.status}`}
                    onChange={(e) => run(() => updateTask(t.id, { status: e.target.value }))}
                  >
                    {STATUSES.map((s) => <option key={s} value={s}>{s}</option>)}
                  </select>
                </td>
                <td>{t.created_at ? new Date(t.created_at + "Z").toLocaleString() : ""}</td>
                <td>
                  <button className="danger" onClick={() => run(() => deleteTask(t.id))}>
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <p className="hint">Auto-refreshes every {POLL_MS / 1000}s. Status must go pending → in-progress → completed.</p>
    </div>
  );
}
