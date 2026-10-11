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

// Feature 5: Search & Filter
export const searchTasks = (filters, skip = 0, limit = 100) =>
  client.post("/tasks/search", filters, { params: { skip, limit } }).then((r) => r.data);

// Feature 6: Reminders
export const getOverdueTasks = () =>
  client.get("/tasks/reminders/overdue").then((r) => r.data);
export const getUpcomingTasks = (daysAhead = 3) =>
  client.get("/tasks/reminders/upcoming", { params: { days_ahead: daysAhead } }).then((r) => r.data);

// Feature 7: Activity
export const getTaskActivity = (taskId) =>
  client.get(`/tasks/${taskId}/activity`).then((r) => r.data);
export const getUserActivitySummary = (limit = 20) =>
  client.get("/tasks/user/activity-summary", { params: { limit } }).then((r) => r.data);

// Feature 8: Subtasks
export const getSubtasks = (taskId) =>
  client.get(`/tasks/${taskId}/subtasks`).then((r) => r.data);
export const createSubtask = (taskId, data) =>
  client.post(`/tasks/${taskId}/subtasks`, data).then((r) => r.data);
export const updateSubtask = (taskId, subtaskId, data) =>
  client.put(`/tasks/${taskId}/subtasks/${subtaskId}`, data).then((r) => r.data);
export const deleteSubtask = (taskId, subtaskId) =>
  client.delete(`/tasks/${taskId}/subtasks/${subtaskId}`);
export const getSubtaskCompletion = (taskId) =>
  client.get(`/tasks/${taskId}/subtasks/completion`).then((r) => r.data);

// Feature 9: Collaboration
export const shareTask = (taskId, email, permission = "view") =>
  client.post(`/tasks/${taskId}/share`, { email, permission }).then((r) => r.data);
export const addComment = (taskId, content) =>
  client.post(`/tasks/${taskId}/comments`, { content }).then((r) => r.data);
export const getComments = (taskId) =>
  client.get(`/tasks/${taskId}/comments`).then((r) => r.data);
export const getSharedTasks = () =>
  client.get("/tasks/shared").then((r) => r.data);

// Feature 10: Export CSV
export const exportCSV = (filters) =>
  client.post("/tasks/export/csv", filters, { responseType: "blob" }).then((r) => r.data);

// Feature A: Task Assignment & Collaborators
export const assignTask = (taskId, email) =>
  client.post(`/tasks/${taskId}/assign`, { email }).then((r) => r.data);
export const addCollaborator = (taskId, email, role = "viewer") =>
  client.post(`/tasks/${taskId}/collaborators`, { email, role }).then((r) => r.data);
export const getCollaborators = (taskId) =>
  client.get(`/tasks/${taskId}/collaborators`).then((r) => r.data);
export const removeCollaborator = (taskId, collaboratorId) =>
  client.delete(`/tasks/${taskId}/collaborators/${collaboratorId}`);
export const getAssignedTasks = () =>
  client.get("/tasks/assigned").then((r) => r.data);

// Notifications
export const getNotifications = (unreadOnly = false, limit = 50) =>
  client.get("/notifications", { params: { unread_only: unreadOnly, limit } }).then((r) => r.data);
export const markNotificationRead = (id) =>
  client.put(`/notifications/${id}/read`).then((r) => r.data);
export const markAllNotificationsRead = () =>
  client.put("/notifications/read-all").then((r) => r.data);

// Feature B: Auth & Profile
export const getProfile = () =>
  client.get("/auth/profile").then((r) => r.data);
export const updateProfile = (data) =>
  client.put("/auth/profile", data).then((r) => r.data);
export const googleLogin = (token) =>
  client.post("/auth/google", { token }).then((r) => r.data);
export const getTimezones = () =>
  client.get("/auth/timezones").then((r) => r.data);

// Feature C: Deadline
export const getTaskDeadline = (taskId) =>
  client.get(`/tasks/${taskId}/deadline`).then((r) => r.data);

// Turn any axios error into a readable string
export function errorMessage(err) {
  if (!err.response) return "Cannot reach the server. Is the backend running?";
  const detail = err.response.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) return detail.map((d) => d.msg).join("; ");
  return `Request failed (${err.response.status})`;
}
