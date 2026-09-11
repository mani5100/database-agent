// frontend/src/pages/ConnectPage.jsx

import { useState } from "react";
import { useSessionStore } from "../store/sessionStore";
import { connectPostgres, connectMysql, connectCsv, connectExcel, connectGoogleSheets } from "../api/connections";
import { getGoogleLoginUrl, searchGoogleSheets } from "../api/googleAuth";

const SOURCE_TYPES = [
  { key: "postgres", label: "PostgreSQL" },
  { key: "mysql", label: "MySQL" },
  { key: "csv", label: "CSV" },
  { key: "excel", label: "Excel" },
  { key: "google_sheets", label: "Google Sheets" },
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
    sheetUrl: "",
  });
  const [file, setFile] = useState(null);
  const [selectedSheet, setSelectedSheet] = useState(null);

  const setConnection = useSessionStore((state) => state.setConnection);
  const goToStep = useSessionStore((state) => state.goToStep);
  const googleSessionId = useSessionStore((state) => state.googleSessionId);

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
      } else if (sourceType === "google_sheets") {
        if (selectedSheet) {
          response = await connectGoogleSheets({
            googleSessionId,
            sheetId: selectedSheet.id,
          });
        } else if (form.sheetUrl) {
          response = await connectGoogleSheets({ sheetUrl: form.sheetUrl });
        } else {
          throw new Error("Paste a public sheet URL, or sign in and pick a sheet.");
        }
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
  const isGoogleSheets = sourceType === "google_sheets";

  return (
    <div>
      <h1 style={{ fontSize: 22, marginBottom: 4 }}>Connect a data source</h1>
      <p style={{ color: "var(--color-muted)", marginBottom: 32 }}>
        Choose where your data lives.
      </p>

      <button
        onClick={() => goToStep("connections")}
        style={{
          marginBottom: 20,
          padding: "6px 12px",
          borderRadius: "var(--radius)",
          border: "1px solid var(--color-border)",
          background: "var(--color-surface)",
          color: "var(--color-muted)",
          fontSize: 13,
        }}
      >
        Switch to an existing connection
      </button>

      <div style={{ display: "flex", gap: 8, marginBottom: 24, flexWrap: "wrap" }}>
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

        {isGoogleSheets && (
          <GoogleSheetsSection
            sheetUrl={form.sheetUrl}
            onUrlChange={(v) => updateField("sheetUrl", v)}
            googleSessionId={googleSessionId}
            selectedSheet={selectedSheet}
            onSelectSheet={setSelectedSheet}
          />
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

function GoogleSheetsSection({ sheetUrl, onUrlChange, googleSessionId, selectedSheet, onSelectSheet }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);

  async function handleLogin() {
    const { auth_url } = await getGoogleLoginUrl();
    window.location.href = auth_url;
  }

  async function handleSearch(e) {
    const value = e.target.value;
    setQuery(value);
    onSelectSheet(null);

    if (!value.trim()) {
      setResults([]);
      return;
    }

    setSearching(true);
    try {
      const response = await searchGoogleSheets(googleSessionId, value);
      setResults(response.sheets);
    } finally {
      setSearching(false);
    }
  }

  if (!googleSessionId) {
    return (
      <div>
        <label style={{ display: "block", fontSize: 13, color: "var(--color-muted)", marginBottom: 6 }}>
          Google Sheets URL (public sheet)
        </label>
        <input
          type="text"
          value={sheetUrl}
          placeholder="https://docs.google.com/spreadsheets/d/..."
          onChange={(e) => onUrlChange(e.target.value)}
          style={{
            width: "100%",
            padding: "8px 12px",
            borderRadius: "var(--radius)",
            border: "1px solid var(--color-border)",
            fontSize: 14,
            marginBottom: 16,
          }}
        />
        <div style={{ padding: "12px 0", borderTop: "1px solid var(--color-border)" }}>
          <button
            type="button"
            onClick={handleLogin}
            style={{
              padding: "8px 16px",
              borderRadius: "var(--radius)",
              border: "1px solid var(--color-border)",
              background: "var(--color-surface)",
              fontSize: 13,
            }}
          >
            Or sign in with Google to browse private sheets
          </button>
        </div>
      </div>
    );
  }

  return (
    <div>
      <label style={{ display: "block", fontSize: 13, color: "var(--color-muted)", marginBottom: 6 }}>
        Search your Google Sheets
      </label>
      <input
        type="text"
        value={query}
        placeholder="Type a sheet name..."
        onChange={handleSearch}
        style={{
          width: "100%",
          padding: "8px 12px",
          borderRadius: "var(--radius)",
          border: "1px solid var(--color-border)",
          fontSize: 14,
          marginBottom: 8,
        }}
      />

      {searching && <div style={{ fontSize: 13, color: "var(--color-muted)" }}>Searching...</div>}

      {!searching && results.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 6, marginBottom: 12 }}>
          {results.map((sheet) => (
            <button
              key={sheet.id}
              type="button"
              onClick={() => onSelectSheet(sheet)}
              style={{
                textAlign: "left",
                padding: "8px 12px",
                borderRadius: "var(--radius)",
                border: selectedSheet?.id === sheet.id ? "1.5px solid var(--color-accent)" : "1px solid var(--color-border)",
                background: "var(--color-surface)",
                fontSize: 13,
              }}
            >
              {sheet.name}
            </button>
          ))}
        </div>
      )}

      {selectedSheet && (
        <div style={{ fontSize: 13, color: "var(--color-accent)", marginBottom: 8 }}>
          Selected: {selectedSheet.name}
        </div>
      )}
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