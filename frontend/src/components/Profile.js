import React, { useEffect, useState } from "react";
import { getProfile, updateProfile, getTimezones, errorMessage } from "../api";
import "../styles/Profile.css";

export default function Profile({ onClose }) {
  const [profile, setProfile] = useState(null);
  const [timezones, setTimezones] = useState([]);
  const [form, setForm] = useState({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    const load = async () => {
      try {
        const [p, tz] = await Promise.all([getProfile(), getTimezones()]);
        setProfile(p);
        setForm({
          username: p.username || "",
          full_name: p.full_name || "",
          bio: p.bio || "",
          timezone: p.timezone || "UTC",
        });
        setTimezones(tz.timezones || []);
      } catch (e) {
        setError(errorMessage(e));
      }
    };
    load();
  }, []);

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      const updates = {};
      if (form.username !== (profile.username || "")) updates.username = form.username || null;
      if (form.full_name !== (profile.full_name || "")) updates.full_name = form.full_name || null;
      if (form.bio !== (profile.bio || "")) updates.bio = form.bio || null;
      if (form.timezone !== (profile.timezone || "UTC")) updates.timezone = form.timezone;

      if (Object.keys(updates).length === 0) {
        setSuccess("No changes to save.");
        setSaving(false);
        return;
      }
      const updated = await updateProfile(updates);
      setProfile(updated);
      setSuccess("Profile updated!");
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setSaving(false);
    }
  };

  if (!profile) {
    return (
      <div className="profile-overlay" onClick={onClose}>
        <div className="profile-panel" onClick={(e) => e.stopPropagation()}>
          <p style={{ padding: "2rem", textAlign: "center", color: "#888" }}>Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="profile-overlay" onClick={onClose}>
      <div className="profile-panel" onClick={(e) => e.stopPropagation()}>
        <div className="profile-header">
          <h2>Profile Settings</h2>
          <button className="profile-close" onClick={onClose}>&times;</button>
        </div>

        <div className="profile-info">
          {profile.profile_picture_url && (
            <img src={profile.profile_picture_url} alt="avatar" className="profile-avatar" />
          )}
          <div className="profile-email">{profile.email}</div>
          {profile.oauth_provider && (
            <span className="profile-badge">Connected via {profile.oauth_provider}</span>
          )}
        </div>

        {error && <div className="profile-alert profile-alert--error">{error}</div>}
        {success && <div className="profile-alert profile-alert--success">{success}</div>}

        <form onSubmit={handleSave} className="profile-form">
          <label className="profile-label">
            Username
            <input
              type="text"
              value={form.username}
              onChange={(e) => setForm({ ...form, username: e.target.value })}
              placeholder="your-username"
              minLength={3}
            />
          </label>

          <label className="profile-label">
            Full Name
            <input
              type="text"
              value={form.full_name}
              onChange={(e) => setForm({ ...form, full_name: e.target.value })}
              placeholder="Your Name"
            />
          </label>

          <label className="profile-label">
            Bio
            <textarea
              value={form.bio}
              onChange={(e) => setForm({ ...form, bio: e.target.value })}
              placeholder="Tell us about yourself..."
              rows={3}
              maxLength={2000}
            />
          </label>

          <label className="profile-label">
            Timezone
            <select
              value={form.timezone}
              onChange={(e) => setForm({ ...form, timezone: e.target.value })}
            >
              {timezones.map((tz) => (
                <option key={tz} value={tz}>{tz}</option>
              ))}
            </select>
          </label>

          <button type="submit" className="profile-save-btn" disabled={saving}>
            {saving ? "Saving..." : "Save Changes"}
          </button>
        </form>
      </div>
    </div>
  );
}
