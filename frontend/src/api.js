import axios from "axios";

// The frontend only talks to the backend through HTTP (no direct DB access).
const client = axios.create({
  baseURL: process.env.REACT_APP_API_URL || "http://localhost:8000",
});

export const getTasks = () => client.get("/tasks/").then((r) => r.data);
export const createTask = (task) => client.post("/tasks/", task).then((r) => r.data);
export const updateTask = (id, changes) =>
  client.put(`/tasks/${id}`, changes).then((r) => r.data);
export const deleteTask = (id) => client.delete(`/tasks/${id}`);

// Turn any axios error into a readable message (handles FastAPI 400/404/422 shapes).
export function errorMessage(err) {
  if (!err.response) return "Cannot reach the server. Is the backend running?";
  const detail = err.response.data && err.response.data.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((d) => d.msg).join("; ");
  return `Request failed (${err.response.status})`;
}
