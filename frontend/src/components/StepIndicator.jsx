// frontend/src/components/StepIndicator.jsx

const STEPS = [
  { key: "connect", label: "Connect" },
  { key: "select", label: "Select tables" },
  { key: "review", label: "Review" },
  { key: "ask", label: "Ask" },
];

function StepIndicator({ currentStep }) {
  const currentIndex = STEPS.findIndex((s) => s.key === currentStep);

  return (
    <div style={{ display: "flex", gap: 8, marginBottom: 40 }}>
      {STEPS.map((step, i) => {
        const isDone = i < currentIndex;
        const isActive = i === currentIndex;
        return (
          <div
            key={step.key}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              flex: 1,
            }}
          >
            <div
              style={{
                width: 24,
                height: 24,
                borderRadius: "50%",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: 12,
                fontWeight: 600,
                flexShrink: 0,
                background: isDone || isActive ? "var(--color-accent)" : "transparent",
                color: isDone || isActive ? "white" : "var(--color-muted)",
                border: isDone || isActive ? "none" : "1px solid var(--color-border)",
              }}
            >
              {i + 1}
            </div>
            <span
              style={{
                fontSize: 13,
                color: isActive ? "var(--color-ink)" : "var(--color-muted)",
                fontWeight: isActive ? 600 : 400,
              }}
            >
              {step.label}
            </span>
            {i < STEPS.length - 1 && (
              <div style={{ flex: 1, height: 1, background: "var(--color-border)" }} />
            )}
          </div>
        );
      })}
    </div>
  );
}

export default StepIndicator;