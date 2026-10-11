import React, { useState } from "react";
import { exportCSV } from "../api";
import "../styles/SearchBar.css";

export default function SearchBar({ onSearch }) {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [priority, setPriority] = useState("");
  const [sortBy, setSortBy] = useState("created_at");
  const [sortOrder, setSortOrder] = useState("desc");
  const [dueDateFrom, setDueDateFrom] = useState("");
  const [dueDateTo, setDueDateTo] = useState("");

  const buildParams = () => {
    const params = {};
    if (search) params.search = search;
    if (status) params.status = status;
    if (priority) params.priority = priority;
    if (sortBy) params.sort_by = sortBy;
    if (sortOrder) params.sort_order = sortOrder;
    if (dueDateFrom) params.due_date_from = dueDateFrom;
    if (dueDateTo) params.due_date_to = dueDateTo;
    return params;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSearch(buildParams());
  };

  const handleClear = () => {
    setSearch("");
    setStatus("");
    setPriority("");
    setSortBy("created_at");
    setSortOrder("desc");
    setDueDateFrom("");
    setDueDateTo("");
    onSearch({});
  };

  const handleExport = async () => {
    try {
      const blob = await exportCSV(buildParams());
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `tasks_${new Date().toISOString().slice(0, 10)}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (e) {
      console.error("Export failed:", e);
    }
  };

  return (
    <form className="search-bar" onSubmit={handleSubmit}>
      <div className="search-bar-row">
        <input
          type="text"
          className="search-input"
          placeholder="Search tasks..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      <div className="filter-grid">
        <div className="filter-group">
          <label>Status</label>
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">All</option>
            <option value="pending">Pending</option>
            <option value="in-progress">In Progress</option>
            <option value="completed">Completed</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Priority</label>
          <select value={priority} onChange={(e) => setPriority(e.target.value)}>
            <option value="">All</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Sort By</label>
          <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
            <option value="created_at">Created Date</option>
            <option value="due_date">Due Date</option>
            <option value="priority">Priority</option>
            <option value="status">Status</option>
            <option value="title">Title</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Order</label>
          <select value={sortOrder} onChange={(e) => setSortOrder(e.target.value)}>
            <option value="desc">Descending</option>
            <option value="asc">Ascending</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Due From</label>
          <input
            type="date"
            value={dueDateFrom}
            onChange={(e) => setDueDateFrom(e.target.value)}
          />
        </div>

        <div className="filter-group">
          <label>Due To</label>
          <input
            type="date"
            value={dueDateTo}
            onChange={(e) => setDueDateTo(e.target.value)}
          />
        </div>
      </div>

      <div className="search-actions">
        <button type="submit" className="search-btn">Search</button>
        <button type="button" className="clear-btn" onClick={handleClear}>Clear Filters</button>
        <button type="button" className="export-btn" onClick={handleExport}>Export CSV</button>
      </div>
    </form>
  );
}
