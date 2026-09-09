// frontend/src/components/ChartRenderer.jsx

import {
  BarChart, Bar,
  LineChart, Line,
  ScatterChart, Scatter,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from "recharts";

const ACCENT = "#0E7C7B";

function ChartRenderer({ rows, candidate }) {
  if (!candidate || !rows || rows.length === 0) return null;

  const { chart_type, x_column, y_columns } = candidate;

  return (
    <div style={{ width: "100%", height: 300, marginTop: 16 }}>
      <ResponsiveContainer>
        {chart_type === "bar" ? (
          <BarChart data={rows}>
            <CartesianGrid stroke="var(--color-border)" vertical={false} />
            <XAxis dataKey={x_column} tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            {y_columns.map((col) => (
              <Bar key={col} dataKey={col} fill={ACCENT} radius={[3, 3, 0, 0]} />
            ))}
          </BarChart>
        ) : chart_type === "line" ? (
          <LineChart data={rows}>
            <CartesianGrid stroke="var(--color-border)" vertical={false} />
            <XAxis dataKey={x_column} tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            {y_columns.map((col) => (
              <Line key={col} type="monotone" dataKey={col} stroke={ACCENT} strokeWidth={2} dot={false} />
            ))}
          </LineChart>
        ) : chart_type === "scatter" ? (
          <ScatterChart>
            <CartesianGrid stroke="var(--color-border)" />
            <XAxis dataKey={x_column} tick={{ fontSize: 12 }} />
            <YAxis dataKey={y_columns[0]} tick={{ fontSize: 12 }} />
            <Tooltip />
            <Scatter data={rows} fill={ACCENT} />
          </ScatterChart>
        ) : null}
      </ResponsiveContainer>
    </div>
  );
}

export default ChartRenderer;