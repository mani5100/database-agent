// frontend/src/pages/ConnectPage.jsx

import { useState } from "react";
import { useSessionStore } from "../store/sessionStore";
import { connectPostgres, connectMysql, connectCsv, connectExcel } from "../api/connections";

const SOURCE_TYPES = [
  { key: "postgres", label: "PostgreSQL" },
  { key: "mysql", label: "MySQL" },
  { key: "csv", label: "CSV" },
  { key: "excel", label: "Excel" },
];

function ConnectPage() {
  const [sourceType, setSourceType] = useState("postgres");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [form, setForm] = useState({
    host: "localhost",
    port: "",
    user: "",
    password: "",
    database: "",
    schema: "public",
  });
  const [file, setFile] = useState(null);

  const setConnection = useSessionStore((state) => state.setConnection);

  function updateField(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      let response;
      if (sourceType === "postgres") {
        response = await connectPostgres({
          host: form.host,
          port: Number(form.port) || 5432,
          user: form.user,
          password: form.password,
          database: form.database,
          schema: form.schema,
        });
      } else if (sourceType === "mysql") {
        response = await connectMysql({
          host: form.host,
          port: Number(form.port) || 3306,
          user: form.user,
          password: form.password,
          database: form.database,
        });
      } else if (sourceType === "csv") {
        if (!file) throw new Error("Choose a CSV file first.");
        response = await connectCsv(file);
      } else if (sourceType === "excel") {
        if (!file) throw new Error("Choose an Excel file first.");
        response = await connectExcel(file);
      }

      setConnection(response.session_id, sourceType);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  const isDatabase = sourceType === "postgres" || sourceType === "mysql";
  const isFile = sourceType === "csv" || sourceType === "excel";

  return (
    <div>
      <h1 style={{ fontSize: 22, marginBottom: 4 }}>Connect a data source</h1>
      <p style={{ color: "var(--color-muted)", marginBottom: 32 }}>
        Choose where your data lives.
      </p>

      <div style={{ display: "flex", gap: 8, marginBottom: 24 }}>
        {SOURCE_TYPES.map((type) => (
          <button
            key={type.key}
            onClick={() => setSourceType(type.key)}
            style={{
              padding: "8px 16px",
              borderRadius: "var(--radius)",
              border: "1px solid var(--color-border)",
              background: sourceType === type.key ? "var(--color-accent)" : "var(--color-surface)",
              color: sourceType === type.key ? "white" : "var(--color-ink)",
              fontSize: 14,
              fontWeight: 500,
            }}
          >
            {type.label}
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit}>
        {isDatabase && (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <Field label="Host" value={form.host} onChange={(v) => updateField("host", v)} />
            <Field label="Port" value={form.port} onChange={(v) => updateField("port", v)} placeholder={sourceType === "postgres" ? "5432" : "3306"} />
            <Field label="User" value={form.user} onChange={(v) => updateField("user", v)} />
            <Field label="Password" type="password" value={form.password} onChange={(v) => updateField("password", v)} />
            <Field label="Database" value={form.database} onChange={(v) => updateField("database", v)} />
            {sourceType === "postgres" && (
              <Field label="Schema" value={form.schema} onChange={(v) => updateField("schema", v)} />
            )}
          </div>
        )}

        {isFile && (
          <div>
            <label style={{ display: "block", fontSize: 13, color: "var(--color-muted)", marginBottom: 6 }}>
              {sourceType === "csv" ? "CSV file" : "Excel file (.xlsx)"}
            </label>
            <input
              type="file"
              accept={sourceType === "csv" ? ".csv" : ".xlsx"}
              onChange={(e) => setFile(e.target.files[0])}
            />
          </div>
        )}

        {error && (
          <div
            style={{
              marginTop: 16,
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
          type="submit"
          disabled={loading}
          style={{
            marginTop: 24,
            padding: "10px 20px",
            borderRadius: "var(--radius)",
            border: "none",
            background: "var(--color-accent)",
            color: "white",
            fontSize: 14,
            fontWeight: 600,
            opacity: loading ? 0.6 : 1,
          }}
        >
          {loading ? "Connecting..." : "Connect"}
        </button>
      </form>
    </div>
  );
}

function Field({ label, value, onChange, type = "text", placeholder }) {
  return (
    <div>
      <label style={{ display: "block", fontSize: 13, color: "var(--color-muted)", marginBottom: 4 }}>
        {label}
      </label>
      <input
        type={type}
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
        style={{
          width: "100%",
          padding: "8px 12px",
          borderRadius: "var(--radius)",
          border: "1px solid var(--color-border)",
          fontSize: 14,
        }}
      />
    </div>
  );
}

export default ConnectPage;