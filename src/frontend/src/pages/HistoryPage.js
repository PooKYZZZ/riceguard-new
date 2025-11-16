// src/pages/HistoryPage.js
import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import "./HistoryPage.css";
import { listScans, buildImageUrl, /* deleteScanSimple, */ bulkDelete } from "../api";

function HistoryPage() {
  const [history, setHistory] = useState([]);
  const [logoutOpen, setLogoutOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState(new Set());
  const [deleteOpen, setDeleteOpen] = useState(false);
  const [deleteMode, setDeleteMode] = useState(null); // 'selected' | 'all'
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  // Load history
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) {
      navigate("/");
      return;
    }
    setLoading(true);
    listScans()
      .then((data) => setHistory(data.items || []))
      .catch((err) => console.error("Error fetching scans:", err))
      .finally(() => setLoading(false));
  }, [navigate]);

  // Derived & local helpers inside render for access to latest state
  const q = query.trim().toLowerCase();
  const visibleHistory = history
    .slice()
    .reverse()
    .filter((item) => {
      if (!q) return true;
      const hay = `${item.label || ""} ${item.createdAt || ""}`.toLowerCase();
      return hay.includes(q);
    });

  const allVisibleSelected =
    visibleHistory.length > 0 &&
    visibleHistory.every((it) => selected.has(it.id));

  const toggleSelect = (id) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleSelectAllVisible = () => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (allVisibleSelected) {
        visibleHistory.forEach((it) => next.delete(it.id));
      } else {
        visibleHistory.forEach((it) => next.add(it.id));
      }
      return next;
    });
  };

  const openDelete = (mode) => {
    setDeleteMode(mode);
    setDeleteOpen(true);
  };

  const confirmDelete = async () => {
    try {
      if (deleteMode === "all") {
        const ids = history.map((h) => h.id);
        if (ids.length === 0) return;
        await bulkDelete(ids);
        setHistory([]);
        setSelected(new Set());
      } else if (deleteMode === "selected") {
        const ids = Array.from(selected);
        if (ids.length === 0) return;
        // use bulk for efficiency
        await bulkDelete(ids);
        setHistory((prev) => prev.filter((it) => !selected.has(it.id)));
        setSelected(new Set());
      }
    } catch (err) {
      console.error("Delete failed:", err);
      alert(err.message || "Delete failed");
    } finally {
      setDeleteOpen(false);
      setDeleteMode(null);
    }
  };

  return (
    <div className="history-page">
      <div className="history-header">
        <div className="logo-section">
          <img
            src={`${process.env.PUBLIC_URL}/logo.png`}
            alt="Rice Guard Logo"
            className="history-logo"
          />
        </div>

        <nav className="nav-links">
          <button onClick={() => setLogoutOpen(true)}>Log Out</button>
          <button onClick={() => navigate("/scan")}>Scan</button>
          <button className="active">History</button>
        </nav>
      </div>

      <div className="history-content">
        <div className="history-toolbar">
          <h2>Scan History</h2>
          <div className="history-controls">
            <input
              className="history-search"
              type="text"
              placeholder="Search history..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
            <label className="select-all">
              <input
                type="checkbox"
                checked={allVisibleSelected}
                onChange={toggleSelectAllVisible}
              />
              <span>Select all</span>
            </label>
            <button
              className="danger"
              disabled={selected.size === 0}
              onClick={() => openDelete("selected")}
            >
              Delete Selected
            </button>
            <button
              className="danger"
              disabled={history.length === 0}
              onClick={() => openDelete("all")}
            >
              Delete All
            </button>
          </div>
        </div>

        {loading ? (
          <p className="loading">Loading…</p>
        ) : history.length === 0 ? (
          <p className="no-history">No history records found.</p>
        ) : (
          <div className="history-grid">
            {visibleHistory.map((item) => (
              <div key={item.id} className="history-card">
                <div className="card-header">
                  <label>
                    <input
                      type="checkbox"
                      checked={selected.has(item.id)}
                      onChange={() => toggleSelect(item.id)}
                    />
                    <span>Select</span>
                  </label>
                </div>
                {item.imageUrl && (
                  <img
                    src={buildImageUrl(item.imageUrl)}
                    alt="Leaf"
                    className="history-image"
                  />
                )}
                <div className="history-info">
                  <h3>{item.label}</h3>
                  <p>
                    <strong>Confidence:</strong>{" "}
                    {typeof item.confidence === "number"
                      ? (item.confidence * 100).toFixed(1)
                      : item.confidence}
                    %
                  </p>
                  <p>
                    <strong>Date:</strong>{" "}
                    {item.createdAt
                      ? new Date(item.createdAt).toLocaleString()
                      : "-"}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}

        {deleteOpen && (
          <div className="modal-backdrop" onClick={() => setDeleteOpen(false)}>
            <div className="modal" onClick={(e) => e.stopPropagation()}>
              <h2>Confirm Delete</h2>
              <p>
                {deleteMode === "all"
                  ? "This will permanently delete all scans."
                  : `Delete ${selected.size} selected scan(s)?`}
              </p>
              <div className="modal-actions">
                <button
                  className="btn-outline"
                  type="button"
                  onClick={() => setDeleteOpen(false)}
                >
                  Cancel
                </button>
                <button
                  className="btn-primary"
                  type="button"
                  onClick={confirmDelete}
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {logoutOpen && (
        <div className="modal-backdrop" onClick={() => setLogoutOpen(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Log out</h2>
            <p>Are you sure you want to log out?</p>
            <div className="modal-actions">
              <button
                className="btn-outline"
                type="button"
                onClick={() => setLogoutOpen(false)}
              >
                Cancel
              </button>
              <button
                className="btn-primary"
                type="button"
                onClick={() => {
                  setLogoutOpen(false);
                  localStorage.removeItem("token");
                  localStorage.removeItem("user");
                  navigate("/");
                }}
              >
                Log out
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default HistoryPage;
