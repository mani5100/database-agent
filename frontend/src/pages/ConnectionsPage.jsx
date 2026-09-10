// frontend/src/pages/ConnectionsPage.jsx

import { useEffect, useState } from "react";
import { useSessionStore } from "../store/sessionStore";
import { listSessions } from "../api/session";

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

  const setActiveSession = useSessionStore((state) => state.setActiveSession);
  const goToStep = useSessionStore((state) => state.goToStep);

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
          <button
            key={session.session_id}
            onClick={() => handleSelect(session)}
            style={{
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