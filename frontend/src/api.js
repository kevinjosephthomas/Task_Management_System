import axios from "axios";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

const client = axios.create({ baseURL: API_URL });

// Attach JWT to every request
client.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
  },
  (error) => Promise.reject(error)
);

// Auto-logout on 401
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("user_email");
      window.location.href = "/";
    }
    return Promise.reject(error);
  }
);

export const getTasks = (params = {}) =>
  client.get("/tasks/", { params }).then((r) => r.data);
export const createTask = (task) =>
  client.post("/tasks/", task).then((r) => r.data);
export const updateTask = (id, changes) =>
  client.put(`/tasks/${id}`, changes).then((r) => r.data);
export const deleteTask = (id) => client.delete(`/tasks/${id}`);
export const getTaskStats = () =>
  client.get("/tasks/stats/summary").then((r) => r.data);

// Turn any axios error into a readable string
export function errorMessage(err) {
  if (!err.response) return "Cannot reach the server. Is the backend running?";
  const detail = err.response.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((d) => d.msg).join("; ");
  return `Request failed (${err.response.status})`;
}
