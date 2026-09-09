// frontend/src/pages/ReviewPage.jsx

import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import { useSessionStore } from "../store/sessionStore";
import { getErd } from "../api/erd";
import ErdDiagram from "../components/ErdDiagram";

function ReviewPage() {
  const sessionId = useSessionStore((state) => state.sessionId);
  const tableNames = useSessionStore((state) => state.tableNames);
  const selectedTables = useSessionStore((state) => state.selectedTables);
  const tableDetails = useSessionStore((state) => state.tableDetails);
  const indexedPoints = useSessionStore((state) => state.indexedPoints);
  const goToStep = useSessionStore((state) => state.goToStep);

  const [activeTab, setActiveTab] = useState("tables");
  const [erd, setErd] = useState(null);
  const [erdError, setErdError] = useState(null);

  useEffect(() => {
    async function loadErd() {
      try {
        const response = await getErd(sessionId);
        setErd(response);
      } catch (err) {
        setErdError(err.message);
      }
    }
    loadErd();
  }, [sessionId]);

  return (
    <div>
      <h1 style={{ fontSize: 22, marginBottom: 4 }}>Semantic layer ready</h1>
      <p style={{ color: "var(--color-muted)", marginBottom: 24 }}>
        {indexedPoints} column{indexedPoints === 1 ? "" : "s"} indexed across {selectedTables.length} table
        {selectedTables.length === 1 ? "" : "s"}.
      </p>

      <div style={{ display: "flex", gap: 4, borderBottom: "1px solid var(--color-border)", marginBottom: 20 }}>
        {[
          { key: "tables", label: "Tables" },
          { key: "diagram", label: "Diagram" },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            style={{
              padding: "8px 14px",
              border: "none",
              background: "none",
              borderBottom: activeTab === tab.key ? "2px solid var(--color-accent)" : "2px solid transparent",
              color: activeTab === tab.key ? "var(--color-ink)" : "var(--color-muted)",
              fontWeight: activeTab === tab.key ? 600 : 400,
              fontSize: 13,
              marginBottom: -1,
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "tables" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 16, marginBottom: 32 }}>
          {selectedTables.map((physicalName) => {
            const detail = tableDetails[physicalName];
            if (!detail) return null;

            return (
              <div
                key={physicalName}
                style={{
                  padding: 16,
                  border: "1px solid var(--color-border)",
                  borderRadius: "var(--radius)",
                  background: "var(--color-surface)",
                }}
              >
                <div style={{ fontWeight: 600, marginBottom: 6 }}>{tableNames[physicalName]}</div>
                <div style={{ fontSize: 14, color: "var(--color-muted)", marginBottom: 10 }}>
                  <ReactMarkdown>{detail.description}</ReactMarkdown>
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                  {detail.columns.map((col) => (
                    <div key={col.physical_name} style={{ fontSize: 13 }}>
                      {col.business_name}
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {activeTab === "diagram" && (
        <div style={{ marginBottom: 32 }}>
          {erdError && (
            <div
              style={{
                padding: 12,
                borderRadius: "var(--radius)",
                background: "var(--color-error-bg)",
                color: "var(--color-error)",
                fontSize: 13,
              }}
            >
              {erdError}
            </div>
          )}
          {erd && <ErdDiagram tables={erd.tables} relationships={erd.relationships} />}
          {!erd && !erdError && (
            <div style={{ color: "var(--color-muted)" }}>Loading diagram...</div>
          )}
        </div>
      )}

      <button
        onClick={() => goToStep("ask")}
        style={{
          padding: "10px 20px",
          borderRadius: "var(--radius)",
          border: "none",
          background: "var(--color-accent)",
          color: "white",
          fontSize: 14,
          fontWeight: 600,
        }}
      >
        Start asking questions
      </button>
    </div>
  );
}

export default ReviewPage;