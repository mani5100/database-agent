// frontend/src/components/StepIndicator.jsx

import { useSessionStore } from "../store/sessionStore";

const STEPS = [
  { key: "connect", label: "Connect" },
  { key: "select", label: "Select tables" },
  { key: "review", label: "Review" },
  { key: "ask", label: "Ask" },
];

function StepIndicator({ currentStep }) {
  const sessionId = useSessionStore((state) => state.sessionId);
  const goToStep = useSessionStore((state) => state.goToStep);

  const currentIndex = STEPS.findIndex((s) => s.key === currentStep);

  return (
    <div style={{ display: "flex", gap: 8, marginBottom: 40 }}>
      {STEPS.map((step, i) => {
        const isDone = i < currentIndex;
        const isActive = i === currentIndex;
        // Connect is always reachable; the rest need an active session to jump to.
        const isReachable = step.key === "connect" || Boolean(sessionId);

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
            <button
              type="button"
              onClick={() => isReachable && goToStep(step.key)}
              disabled={!isReachable}
              title={isReachable ? undefined : "Connect to a data source first"}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                border: "none",
                background: "none",
                padding: 0,
                cursor: isReachable ? "pointer" : "not-allowed",
                opacity: isReachable ? 1 : 0.5,
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
            </button>
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