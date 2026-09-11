// frontend/src/pages/ConnectionsPage.jsx

import { useEffect, useState } from "react";
import { useSessionStore } from "../store/sessionStore";
import { listSessions } from "../api/session";
import { closeSession } from "../api/connections";

const SOURCE_LABELS = {
  postgres: "PostgreSQL",
  mysql: "MySQL",
  csv: "CSV",
  excel: "Excel",
};

function ConnectionsPage() {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deletingId, setDeletingId] = useState(null);

  const activeSessionId = useSessionStore((state) => state.sessionId);
  const setActiveSession = useSessionStore((state) => state.setActiveSession);
  const goToStep = useSessionStore((state) => state.goToStep);
  const reset = useSessionStore((state) => state.reset);

  useEffect(() => {
    async function load() {
      try {
        const response = await listSessions();
        setSessions(response.sessions);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  function handleSelect(session) {
    setActiveSession(session.session_id, session.source_type);
    goToStep("select");
  }

  async function handleDelete(e, session) {
    e.stopPropagation();
    if (!window.confirm("Close this connection? This cannot be undone.")) return;

    setError(null);
    setDeletingId(session.session_id);
    try {
      await closeSession(session.session_id);
      setSessions((prev) => prev.filter((s) => s.session_id !== session.session_id));
      if (session.session_id === activeSessionId) {
        reset();
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div>
      <h1 style={{ fontSize: 22, marginBottom: 4 }}>Active connections</h1>
      <p style={{ color: "var(--color-muted)", marginBottom: 24 }}>
        Switch to a previously connected data source.
      </p>

      {loading && <div style={{ color: "var(--color-muted)" }}>Loading...</div>}

      {error && (
        <div
          style={{
            padding: 12,
            borderRadius: "var(--radius)",
            background: "var(--color-error-bg)",
            color: "var(--color-error)",
            fontSize: 13,
          }}
        >
          {error}
        </div>
      )}

      {!loading && !error && sessions.length === 0 && (
        <div style={{ color: "var(--color-muted)" }}>No active connections found.</div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 24 }}>
        {sessions.map((session) => (
          <div key={session.session_id} style={{ display: "flex", gap: 8 }}>
            <button
              onClick={() => handleSelect(session)}
              style={{
                flex: 1,
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                padding: "12px 16px",
                border: "1px solid var(--color-border)",
                borderRadius: "var(--radius)",
                background: "var(--color-surface)",
                textAlign: "left",
                fontSize: 14,
              }}
            >
              <span style={{ fontWeight: 500 }}>{SOURCE_LABELS[session.source_type] || session.source_type}</span>
              <span className="mono" style={{ fontSize: 12, color: "var(--color-muted)" }}>
                {session.session_id.slice(0, 8)}
              </span>
            </button>
            <button
              onClick={(e) => handleDelete(e, session)}
              disabled={deletingId === session.session_id}
              title="Close connection"
              style={{
                padding: "12px 16px",
                border: "1px solid var(--color-border)",
                borderRadius: "var(--radius)",
                background: "var(--color-surface)",
                color: "var(--color-error)",
                fontSize: 13,
                opacity: deletingId === session.session_id ? 0.6 : 1,
              }}
            >
              {deletingId === session.session_id ? "..." : "Close"}
            </button>
          </div>
        ))}
      </div>

      <button
        onClick={() => goToStep("connect")}
        style={{
          padding: "10px 20px",
          borderRadius: "var(--radius)",
          border: "1px solid var(--color-border)",
          background: "var(--color-surface)",
          color: "var(--color-ink)",
          fontSize: 14,
          fontWeight: 500,
        }}
      >
        Back to new connection
      </button>
    </div>
  );
}

export default ConnectionsPage;