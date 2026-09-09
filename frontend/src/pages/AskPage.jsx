// frontend/src/pages/AskPage.jsx

import { useState } from "react";
import { useSessionStore } from "../store/sessionStore";
import { askQuestion } from "../api/agent";
import ResultTable from "../components/ResultTable";
import ChartRenderer from "../components/ChartRenderer";
import ChartCandidateList from "../components/ChartCandidateList";
import ReactMarkdown from "react-markdown";

function AskPage() {
  const sessionId = useSessionStore((state) => state.sessionId);
  const chatHistory = useSessionStore((state) => state.chatHistory);
  const addChatEntry = useSessionStore((state) => state.addChatEntry);

  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!question.trim()) return;

    setError(null);
    setLoading(true);

    try {
      const response = await askQuestion(sessionId, question);
      const defaultCandidate = response.chart_candidates.find((c) => c.is_default);

      addChatEntry({
        question: response.question,
        sql: response.sql,
        answer: response.answer,
        resultRows: response.result_rows,
        chartCandidates: response.chart_candidates,
        selectedChartId: defaultCandidate ? defaultCandidate.chart_id : null,
      });
      setQuestion("");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h1 style={{ fontSize: 22, marginBottom: 4 }}>Ask a question</h1>
      <p style={{ color: "var(--color-muted)", marginBottom: 24 }}>
        Ask anything about the connected data.
      </p>

      <div style={{ display: "flex", flexDirection: "column", gap: 24, marginBottom: 24 }}>
        {chatHistory.map((entry, i) => (
          <ChatEntry key={i} entry={entry} />
        ))}
      </div>

      {error && (
        <div
          style={{
            marginBottom: 16,
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

      <form onSubmit={handleSubmit} style={{ display: "flex", gap: 8 }}>
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="e.g. What is the total revenue by customer?"
          disabled={loading}
          style={{
            flex: 1,
            padding: "10px 14px",
            borderRadius: "var(--radius)",
            border: "1px solid var(--color-border)",
            fontSize: 14,
          }}
        />
        <button
          type="submit"
          disabled={loading}
          style={{
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
          {loading ? "Thinking..." : "Ask"}
        </button>
      </form>
    </div>
  );
}

function ChatEntry({ entry }) {
  const [activeTab, setActiveTab] = useState("answer");
  const [selectedChartId, setSelectedChartId] = useState(entry.selectedChartId);

  const selectedCandidate = entry.chartCandidates.find((c) => c.chart_id === selectedChartId);

  const TABS = [
    { key: "answer", label: "Answer" },
    { key: "query", label: "Query" },
    { key: "table", label: "Table" },
    ...(entry.chartCandidates.length > 0 ? [{ key: "chart", label: "Chart" }] : []),
  ];

  return (
    <div
      style={{
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius)",
        background: "var(--color-surface)",
        overflow: "hidden",
      }}
    >
      <div style={{ padding: "16px 16px 0" }}>
        <p style={{ fontWeight: 600, marginBottom: 14 }}>{entry.question}</p>
        <div style={{ display: "flex", gap: 4, borderBottom: "1px solid var(--color-border)" }}>
          {TABS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              style={{
                padding: "8px 14px",
                border: "none",
                background: "none",
                borderBottom: activeTab === tab.key ? "2px solid var(--color-accent)" : "2px solid transparent",
                color: activeTab === tab.key ? "var(--color-ink)" : "var(--color-muted)",
                fontWeight: activeTab === tab.key ? 600 : 400,
                fontSize: 13,
                marginBottom: -1,
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      <div style={{ padding: 16 }}>
        {activeTab === "answer" && (
  <div style={{ lineHeight: 1.6 }}>
    <ReactMarkdown>{entry.answer}</ReactMarkdown>
  </div>
)}

        {activeTab === "query" && (
          <pre
            className="mono"
            style={{
              margin: 0,
              fontSize: 13,
              whiteSpace: "pre-wrap",
              wordBreak: "break-word",
              color: "var(--color-ink)",
              background: "var(--color-bg)",
              padding: 12,
              borderRadius: "var(--radius)",
              border: "1px solid var(--color-border)",
            }}
          >
            {entry.sql || "No query recorded."}
          </pre>
        )}

        {activeTab === "table" && <ResultTable rows={entry.resultRows} />}

        {activeTab === "chart" && (
          <>
            {selectedCandidate && (
              <ChartRenderer rows={entry.resultRows} candidate={selectedCandidate} />
            )}
            <ChartCandidateList
              candidates={entry.chartCandidates}
              selectedId={selectedChartId}
              onSelect={setSelectedChartId}
            />
          </>
        )}
      </div>
    </div>
  );
}

export default AskPage;