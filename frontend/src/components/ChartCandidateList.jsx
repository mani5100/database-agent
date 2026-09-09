// frontend/src/components/ChartCandidateList.jsx

function ChartCandidateList({ candidates, selectedId, onSelect }) {
  if (!candidates || candidates.length <= 1) return null;

  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 12, marginTop: 12 }}>
      {candidates.map((candidate) => (
        <label
          key={candidate.chart_id}
          style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13 }}
        >
          <input
            type="radio"
            name="chart-candidate"
            checked={selectedId === candidate.chart_id}
            onChange={() => onSelect(candidate.chart_id)}
          />
          {candidate.label}
        </label>
      ))}
    </div>
  );
}

export default ChartCandidateList;