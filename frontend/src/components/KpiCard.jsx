// frontend/src/components/KpiCard.jsx

function formatLabel(key) {
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatValue(value) {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "number") {
    return Number.isInteger(value)
      ? value.toLocaleString()
      : value.toLocaleString(undefined, { maximumFractionDigits: 2 });
  }
  const asNumber = Number(value);
  if (!Number.isNaN(asNumber) && value.toString().trim() !== "") {
    return formatValue(asNumber);
  }
  return String(value);
}

function KpiCard({ rows }) {
  if (!rows || rows.length === 0) return null;

  const row = rows[0];
  const columns = Object.keys(row);
  if (columns.length === 0) return null;

  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 12, marginTop: 4 }}>
      {columns.map((col) => (
        <div
          key={col}
          style={{
            flex: "1 1 160px",
            minWidth: 160,
            padding: "18px 20px",
            borderRadius: "var(--radius)",
            border: "1px solid var(--color-border)",
            background: "var(--color-surface)",
          }}
        >
          <div
            style={{
              fontSize: 12,
              fontWeight: 600,
              color: "var(--color-muted)",
              textTransform: "uppercase",
              letterSpacing: 0.4,
              marginBottom: 8,
            }}
          >
            {formatLabel(col)}
          </div>
          <div
            className="mono"
            style={{
              fontSize: 32,
              fontWeight: 700,
              color: "var(--color-accent)",
              lineHeight: 1.1,
            }}
          >
            {formatValue(row[col])}
          </div>
        </div>
      ))}
    </div>
  );
}

export default KpiCard;
