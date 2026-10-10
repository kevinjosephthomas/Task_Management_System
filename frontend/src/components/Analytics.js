import React, { useEffect, useState } from "react";
import {
  BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";
import { getTaskStats, errorMessage } from "../api";
import "../styles/Analytics.css";

const STATUS_COLORS = ["#6c757d", "#f0a500", "#28a745"];
const PRIORITY_COLORS = { High: "#dc3545", Medium: "#fd7e14", Low: "#20c997" };

export default function Analytics() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadStats = async () => {
    try {
      const data = await getTaskStats();
      setStats(data);
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStats();
    const timer = setInterval(loadStats, 10000);
    return () => clearInterval(timer);
  }, []);

  if (loading) return <div className="analytics-loading"><span className="spinner" />Loading analytics…</div>;
  if (error) return <div className="analytics-error">{error}</div>;
  if (!stats) return null;

  const statusData = [
    { name: "Pending",     value: stats.pending },
    { name: "In Progress", value: stats.in_progress },
    { name: "Completed",   value: stats.completed },
  ];

  const priorityData = [
    { name: "High",   value: stats.by_priority.high },
    { name: "Medium", value: stats.by_priority.medium },
    { name: "Low",    value: stats.by_priority.low },
  ];

  const statCards = [
    { label: "Total",      value: stats.total_tasks,           icon: "📋", accent: "#667eea" },
    { label: "Pending",    value: stats.pending,               icon: "⏳", accent: "#6c757d" },
    { label: "In Progress",value: stats.in_progress,           icon: "🔄", accent: "#f0a500" },
    { label: "Completed",  value: stats.completed,             icon: "✅", accent: "#28a745" },
    { label: "Overdue",    value: stats.overdue,               icon: "🚨", accent: stats.overdue > 0 ? "#dc3545" : "#28a745" },
    { label: "Completion", value: `${stats.completion_percentage}%`, icon: "📈", accent: "#667eea" },
  ];

  return (
    <div className="analytics-container">
      <h2>📊 Analytics Dashboard</h2>

      <div className="stats-grid">
        {statCards.map(({ label, value, icon, accent }) => (
          <div key={label} className="stat-card" style={{ borderTopColor: accent }}>
            <div className="stat-icon">{icon}</div>
            <div className="stat-value" style={{ color: accent }}>{value}</div>
            <div className="stat-label">{label}</div>
          </div>
        ))}
      </div>

      <div className="charts-grid">
        <div className="chart-card">
          <h3>Status Distribution</h3>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie
                data={statusData}
                cx="50%" cy="50%"
                outerRadius={90}
                dataKey="value"
                label={({ name, value }) => value > 0 ? `${name}: ${value}` : ""}
              >
                {statusData.map((_, i) => (
                  <Cell key={i} fill={STATUS_COLORS[i]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h3>By Priority</h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={priorityData} barSize={50}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="name" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                {priorityData.map(({ name }, i) => (
                  <Cell key={i} fill={PRIORITY_COLORS[name]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="chart-card completion-card">
        <h3>Overall Completion</h3>
        <div className="progress-track">
          <div
            className="progress-fill"
            style={{ width: `${stats.completion_percentage}%` }}
          >
            {stats.completion_percentage > 5 && `${stats.completion_percentage}%`}
          </div>
        </div>
        <p className="completion-caption">
          {stats.completed} of {stats.total_tasks} tasks completed
        </p>
      </div>
    </div>
  );
}
