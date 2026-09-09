// frontend/src/components/ResultTable.jsx

function ResultTable({ rows }) {
  if (!rows || rows.length === 0) return null;

  const columns = Object.keys(rows[0]);

  return (
    <div style={{ overflowX: "auto", marginTop: 12 }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
        <thead>
          <tr>
            {columns.map((col) => (
              <th
                key={col}
                className="mono"
                style={{
                  textAlign: "left",
                  padding: "8px 12px",
                  borderBottom: "1px solid var(--color-border)",
                  color: "var(--color-muted)",
                  fontWeight: 500,
                }}
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              {columns.map((col) => (
                <td
                  key={col}
                  style={{
                    padding: "8px 12px",
                    borderBottom: "1px solid var(--color-border)",
                  }}
                >
                  {String(row[col] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default ResultTable;