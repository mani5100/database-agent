// frontend/src/pages/TableSelectionPage.jsx

import { useEffect, useState } from "react";
import { useSessionStore } from "../store/sessionStore";
import { generateTableNames, generateTableDetails, assembleSemanticLayer } from "../api/semanticLayer";

function TableSelectionPage() {
  const sessionId = useSessionStore((state) => state.sessionId);
  const tableNames = useSessionStore((state) => state.tableNames);
  const selectedTables = useSessionStore((state) => state.selectedTables);
  const setTableNames = useSessionStore((state) => state.setTableNames);
  const toggleTableSelection = useSessionStore((state) => state.toggleTableSelection);
  const setTableDetail = useSessionStore((state) => state.setTableDetail);
  const tableDetails = useSessionStore((state) => state.tableDetails);
  const setAssemblyResult = useSessionStore((state) => state.setAssemblyResult);

  const [loadingNames, setLoadingNames] = useState(true);
  const [error, setError] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [currentlyGenerating, setCurrentlyGenerating] = useState(null);

  useEffect(() => {
    async function load() {
      try {
        const response = await generateTableNames(sessionId);
        setTableNames(response.table_names);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoadingNames(false);
      }
    }
    load();
  }, [sessionId, setTableNames]);

  async function handleGenerate() {
    setError(null);
    setGenerating(true);

    try {
      for (const physicalName of selectedTables) {
        setCurrentlyGenerating(physicalName);
        const detail = await generateTableDetails(sessionId, physicalName);
        setTableDetail(physicalName, detail);
      }

      const result = await assembleSemanticLayer(sessionId, selectedTables);
      setAssemblyResult(result.file_path, result.indexed_points);
    } catch (err) {
      setError(err.message);
    } finally {
      setGenerating(false);
      setCurrentlyGenerating(null);
    }
  }

  if (loadingNames) {
    return <div style={{ color: "var(--color-muted)" }}>Loading tables...</div>;
  }

  const physicalNames = Object.keys(tableNames);

  return (
    <div>
      <h1 style={{ fontSize: 22, marginBottom: 4 }}>Select tables</h1>
      <p style={{ color: "var(--color-muted)", marginBottom: 24 }}>
        Choose which tables to include in the semantic layer.
      </p>

      <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 24 }}>
        {physicalNames.map((physicalName) => {
          const isSelected = selectedTables.includes(physicalName);
          const isDone = Boolean(tableDetails[physicalName]);
          const isCurrent = currentlyGenerating === physicalName;

          return (
            <label
              key={physicalName}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 10,
                padding: "10px 14px",
                border: "1px solid var(--color-border)",
                borderRadius: "var(--radius)",
                background: "var(--color-surface)",
                cursor: generating ? "default" : "pointer",
              }}
            >
              <input
                type="checkbox"
                checked={isSelected}
                disabled={generating}
                onChange={() => toggleTableSelection(physicalName)}
              />
              <span style={{ fontWeight: 500 }}>{tableNames[physicalName]}</span>
              <span className="mono" style={{ fontSize: 12, color: "var(--color-muted)" }}>
                {physicalName}
              </span>
              {isCurrent && (
                <span style={{ marginLeft: "auto", fontSize: 12, color: "var(--color-accent)" }}>
                  Generating...
                </span>
              )}
              {isDone && !isCurrent && (
                <span style={{ marginLeft: "auto", fontSize: 12, color: "var(--color-accent)" }}>
                  Done
                </span>
              )}
            </label>
          );
        })}
      </div>

      {error && (
        <div
          style={{
            marginBottom: 16,
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

      <button
        onClick={handleGenerate}
        disabled={selectedTables.length === 0 || generating}
        style={{
          padding: "10px 20px",
          borderRadius: "var(--radius)",
          border: "none",
          background: "var(--color-accent)",
          color: "white",
          fontSize: 14,
          fontWeight: 600,
          opacity: selectedTables.length === 0 || generating ? 0.6 : 1,
        }}
      >
        {generating ? "Generating semantic layer..." : "Generate semantic layer"}
      </button>
    </div>
  );
}

export default TableSelectionPage;