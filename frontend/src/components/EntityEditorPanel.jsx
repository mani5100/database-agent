// frontend/src/components/EntityEditorPanel.jsx

import { useState } from "react";
import { updateEntity } from "../api/erd";

const inputStyle = {
  width: "100%",
  padding: "6px 8px",
  borderRadius: "var(--radius)",
  border: "1px solid var(--color-border)",
  background: "var(--color-bg)",
  color: "var(--color-ink)",
  fontSize: 13,
  fontFamily: "var(--font-sans)",
};

const labelStyle = { fontSize: 12, color: "var(--color-muted)", marginBottom: 4 };

function EntityEditorPanel({ sessionId, table, onClose, onSaved }) {
  const [name, setName] = useState(table.name);
  const [description, setDescription] = useState(table.description || "");
  const [columns, setColumns] = useState(
    table.columns.map((col) => ({
      physical_name: col.physical_name,
      name: col.name,
      description: col.description || "",
    }))
  );
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  function updateColumn(physicalName, field, value) {
    setColumns((prev) =>
      prev.map((col) => (col.physical_name === physicalName ? { ...col, [field]: value } : col))
    );
  }

  async function handleSave() {
    setSubmitting(true);
    setError(null);
    try {
      await updateEntity(sessionId, table.physical_name, {
        name: name.trim(),
        description,
        columns: columns.map((col) => ({ ...col, name: col.name.trim() })),
      });
      await onSaved();
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  const canSave = name.trim() && columns.every((col) => col.name.trim());

  return (
    <div
      onClick={onClose}
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(20, 23, 26, 0.35)",
        display: "flex",
        justifyContent: "flex-end",
        zIndex: 1000,
      }}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          width: 420,
          maxWidth: "100%",
          height: "100%",
          overflowY: "auto",
          padding: 20,
          background: "var(--color-surface)",
          borderLeft: "1px solid var(--color-border)",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
          <div style={{ fontWeight: 600, fontSize: 16 }}>Edit entity</div>
          <button
            onClick={onClose}
            style={{ border: "none", background: "none", fontSize: 18, color: "var(--color-muted)" }}
          >
            ×
          </button>
        </div>
        <div style={{ fontSize: 12, color: "var(--color-muted)", marginBottom: 16 }}>
          Physical table: <span className="mono">{table.physical_name}</span>
        </div>

        {error && (
          <div
            style={{
              padding: 10,
              marginBottom: 12,
              borderRadius: "var(--radius)",
              background: "var(--color-error-bg)",
              color: "var(--color-error)",
              fontSize: 13,
            }}
          >
            {error}
          </div>
        )}

        <div style={{ marginBottom: 12 }}>
          <div style={labelStyle}>Business name</div>
          <input value={name} onChange={(e) => setName(e.target.value)} style={inputStyle} />
        </div>
        <div style={{ marginBottom: 20 }}>
          <div style={labelStyle}>Description</div>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={4}
            style={{ ...inputStyle, resize: "vertical" }}
          />
        </div>

        <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 10 }}>Columns</div>
        <div style={{ display: "flex", flexDirection: "column", gap: 12, marginBottom: 20 }}>
          {columns.map((col) => (
            <div
              key={col.physical_name}
              style={{ padding: 10, border: "1px solid var(--color-border)", borderRadius: "var(--radius)" }}
            >
              <div style={labelStyle}>Business name</div>
              <input
                value={col.name}
                onChange={(e) => updateColumn(col.physical_name, "name", e.target.value)}
                style={{ ...inputStyle, marginBottom: 6 }}
              />
              <div style={labelStyle}>Description</div>
              <textarea
                value={col.description}
                onChange={(e) => updateColumn(col.physical_name, "description", e.target.value)}
                rows={2}
                style={{ ...inputStyle, resize: "vertical" }}
              />
            </div>
          ))}
        </div>

        <div style={{ display: "flex", gap: 8 }}>
          <button
            onClick={handleSave}
            disabled={!canSave || submitting}
            style={{
              padding: "8px 16px",
              borderRadius: "var(--radius)",
              border: "none",
              background: "var(--color-accent)",
              color: "white",
              fontSize: 13,
              fontWeight: 600,
              opacity: !canSave || submitting ? 0.6 : 1,
            }}
          >
            {submitting ? "Saving..." : "Save"}
          </button>
          <button
            onClick={onClose}
            style={{
              padding: "8px 16px",
              borderRadius: "var(--radius)",
              border: "1px solid var(--color-border)",
              background: "var(--color-bg)",
              color: "var(--color-ink)",
              fontSize: 13,
            }}
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}

export default EntityEditorPanel;
