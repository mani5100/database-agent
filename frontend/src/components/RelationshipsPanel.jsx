// frontend/src/components/RelationshipsPanel.jsx

import { useEffect, useState } from "react";
import {
  createRelationship,
  deleteRelationship,
  getRelationships,
  updateRelationship,
} from "../api/relationships";

const REL_TYPES = [
  { value: "many_to_one", label: "Many → One" },
  { value: "one_to_many", label: "One → Many" },
  { value: "one_to_one", label: "One → One" },
];

const EMPTY_FORM = {
  from_table: "",
  from_column: "",
  to_table: "",
  to_column: "",
  type: "many_to_one",
  description: "",
};

function columnsFor(tables, tableName) {
  const table = tables.find((t) => t.name === tableName);
  return table ? table.columns : [];
}

function RelationshipsPanel({ sessionId, tables, onChange }) {
  const [relationships, setRelationships] = useState([]);
  const [error, setError] = useState(null);
  const [editingName, setEditingName] = useState(null); // null = add mode
  const [form, setForm] = useState(EMPTY_FORM);
  const [submitting, setSubmitting] = useState(false);
  const [formOpen, setFormOpen] = useState(false);

  async function loadRelationships() {
    try {
      const response = await getRelationships(sessionId);
      setRelationships(response.relationships);
    } catch (err) {
      setError(err.message);
    }
  }

  useEffect(() => {
    loadRelationships();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sessionId]);

  function updateField(field, value) {
    setForm((prev) => {
      const next = { ...prev, [field]: value };
      if (field === "from_table") next.from_column = "";
      if (field === "to_table") next.to_column = "";
      return next;
    });
  }

  function startEdit(rel) {
    setEditingName(rel.name);
    setForm({
      from_table: rel.from_model,
      from_column: rel.from_column,
      to_table: rel.to_model,
      to_column: rel.to_column,
      type: rel.type,
      description: rel.description || "",
    });
    setError(null);
    setFormOpen(true);
  }

  function cancelEdit() {
    setEditingName(null);
    setForm(EMPTY_FORM);
    setError(null);
    setFormOpen(false);
  }

  async function handleDelete(name) {
    setError(null);
    try {
      await deleteRelationship(sessionId, name);
      if (editingName === name) cancelEdit();
      await loadRelationships();
      await onChange();
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);

    const payload = {
      from_model: form.from_table,
      from_column: form.from_column,
      to_model: form.to_table,
      to_column: form.to_column,
      type: form.type,
      description: form.description || undefined,
    };

    try {
      if (editingName) {
        await updateRelationship(sessionId, editingName, payload);
      } else {
        await createRelationship(sessionId, payload);
      }
      cancelEdit();
      await loadRelationships();
      await onChange();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  }

  const fromColumns = columnsFor(tables, form.from_table);
  const toColumns = columnsFor(tables, form.to_table);
  const canSubmit = form.from_table && form.from_column && form.to_table && form.to_column;

  return (
    <div
      style={{
        marginTop: 16,
        padding: 16,
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius)",
        background: "var(--color-surface)",
      }}
    >
      <div style={{ fontWeight: 600, marginBottom: 12 }}>Relationships</div>

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

      <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 16 }}>
        {relationships.length === 0 && (
          <div style={{ fontSize: 13, color: "var(--color-muted)" }}>No relationships defined yet.</div>
        )}
        {relationships.map((rel) => (
          <div
            key={rel.name}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: 8,
              padding: "8px 10px",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius)",
              fontSize: 13,
            }}
          >
            <div>
              <span className="mono">
                {rel.from_model}.{rel.from_column}
              </span>{" "}
              → <span className="mono">
                {rel.to_model}.{rel.to_column}
              </span>{" "}
              <span style={{ color: "var(--color-muted)" }}>({rel.type})</span>
              {rel.description && (
                <div style={{ color: "var(--color-muted)", marginTop: 2 }}>{rel.description}</div>
              )}
            </div>
            <div style={{ display: "flex", gap: 6, flexShrink: 0 }}>
              <button
                onClick={() => startEdit(rel)}
                style={{
                  padding: "4px 10px",
                  borderRadius: "var(--radius)",
                  border: "1px solid var(--color-border)",
                  background: "var(--color-bg)",
                  color: "var(--color-ink)",
                  fontSize: 12,
                }}
              >
                Edit
              </button>
              <button
                onClick={() => handleDelete(rel.name)}
                style={{
                  padding: "4px 10px",
                  borderRadius: "var(--radius)",
                  border: "1px solid var(--color-border)",
                  background: "var(--color-bg)",
                  color: "var(--color-error)",
                  fontSize: 12,
                }}
              >
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>

      {!formOpen && (
        <button
          type="button"
          onClick={() => setFormOpen(true)}
          style={{
            padding: "8px 16px",
            borderRadius: "var(--radius)",
            border: "1px solid var(--color-border)",
            background: "var(--color-bg)",
            color: "var(--color-accent)",
            fontSize: 13,
            fontWeight: 600,
          }}
        >
          + Add relationship
        </button>
      )}

      {formOpen && (
        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <div style={{ fontSize: 13, fontWeight: 600 }}>
            {editingName ? "Edit relationship" : "Add relationship"}
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
            <TableColumnGroup
              label="From"
              tables={tables}
              tableValue={form.from_table}
              columnValue={form.from_column}
              columns={fromColumns}
              onTableChange={(v) => updateField("from_table", v)}
              onColumnChange={(v) => updateField("from_column", v)}
            />

            <div style={{ fontSize: 18, color: "var(--color-muted)", paddingTop: 14 }}>→</div>

            <TableColumnGroup
              label="To"
              tables={tables}
              tableValue={form.to_table}
              columnValue={form.to_column}
              columns={toColumns}
              onTableChange={(v) => updateField("to_table", v)}
              onColumnChange={(v) => updateField("to_column", v)}
            />
          </div>

          <div>
            <div style={{ fontSize: 12, color: "var(--color-muted)", marginBottom: 6 }}>Relationship type</div>
            <div style={{ display: "flex", gap: 6 }}>
              {REL_TYPES.map((t) => (
                <button
                  key={t.value}
                  type="button"
                  onClick={() => updateField("type", t.value)}
                  style={{
                    padding: "6px 12px",
                    borderRadius: "var(--radius)",
                    border: form.type === t.value ? "1px solid var(--color-accent)" : "1px solid var(--color-border)",
                    background: form.type === t.value ? "var(--color-accent)" : "var(--color-bg)",
                    color: form.type === t.value ? "white" : "var(--color-ink)",
                    fontSize: 12,
                    fontWeight: 500,
                  }}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>

          <Field label="Description (optional)">
            <input
              type="text"
              value={form.description}
              onChange={(e) => updateField("description", e.target.value)}
              placeholder="e.g. Each order belongs to one customer"
              style={{ ...selectStyle, width: "100%" }}
            />
          </Field>

          <div style={{ display: "flex", gap: 8 }}>
            <button
              type="submit"
              disabled={!canSubmit || submitting}
              style={{
                padding: "8px 16px",
                borderRadius: "var(--radius)",
                border: "none",
                background: "var(--color-accent)",
                color: "white",
                fontSize: 13,
                fontWeight: 600,
                opacity: !canSubmit || submitting ? 0.6 : 1,
              }}
            >
              {editingName ? "Save changes" : "Add relationship"}
            </button>
            <button
              type="button"
              onClick={cancelEdit}
              style={{
                padding: "8px 16px",
                borderRadius: "var(--radius)",
                border: "1px solid var(--color-border)",
                background: "var(--color-bg)",
                color: "var(--color-ink)",
                fontSize: 13,
              }}
            >
              {editingName ? "Cancel edit" : "Cancel"}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}

const selectStyle = {
  padding: "8px 10px",
  borderRadius: "var(--radius)",
  border: "1px solid var(--color-border)",
  background: "var(--color-surface)",
  color: "var(--color-ink)",
  fontSize: 13,
};

function Field({ label, children }) {
  return (
    <label style={{ display: "flex", flexDirection: "column", gap: 4, fontSize: 12, color: "var(--color-muted)" }}>
      {label}
      {children}
    </label>
  );
}

function TableColumnGroup({ label, tables, tableValue, columnValue, columns, onTableChange, onColumnChange }) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 6,
        padding: 10,
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius)",
        background: "var(--color-bg)",
        minWidth: 180,
        flex: "1 1 200px",
      }}
    >
      <div style={{ fontSize: 12, fontWeight: 600, color: "var(--color-accent)" }}>{label}</div>
      <select value={tableValue} onChange={(e) => onTableChange(e.target.value)} style={selectStyle}>
        <option value="">Select table</option>
        {tables.map((t) => (
          <option key={t.name} value={t.name}>
            {t.name}
          </option>
        ))}
      </select>
      <select
        value={columnValue}
        onChange={(e) => onColumnChange(e.target.value)}
        disabled={!tableValue}
        style={selectStyle}
      >
        <option value="">Select column</option>
        {columns.map((c) => (
          <option key={c.name} value={c.name}>
            {c.name}
          </option>
        ))}
      </select>
    </div>
  );
}

export default RelationshipsPanel;
