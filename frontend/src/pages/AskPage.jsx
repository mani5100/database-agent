// frontend/src/pages/AskPage.jsx

import { useEffect, useState } from "react";
import { useSessionStore } from "../store/sessionStore";
import { askQuestion } from "../api/agent";
import { createChat, listChats, getChatHistory } from "../api/chats";
import ResultTable from "../components/ResultTable";
import ChartRenderer from "../components/ChartRenderer";
import ChartCandidateList from "../components/ChartCandidateList";
import KpiCard from "../components/KpiCard";
import ReactMarkdown from "react-markdown";

function toEntry(message) {
  const candidates = message.chart_candidates || [];
  const defaultCandidate = candidates.find((c) => c.is_default);
  return {
    question: message.question,
    sql: message.sql,
    answer: message.answer,
    resultRows: message.result_rows,
    chartCandidates: candidates,
    selectedChartId: defaultCandidate ? defaultCandidate.chart_id : null,
  };
}

function AskPage() {
  const sessionId = useSessionStore((state) => state.sessionId);
  const chats = useSessionStore((state) => state.chats);
  const activeChatId = useSessionStore((state) => state.activeChatId);
  const chatMessages = useSessionStore((state) => state.chatMessages);
  const setChats = useSessionStore((state) => state.setChats);
  const addChat = useSessionStore((state) => state.addChat);
  const setActiveChatId = useSessionStore((state) => state.setActiveChatId);
  const setChatMessages = useSessionStore((state) => state.setChatMessages);
  const addChatMessage = useSessionStore((state) => state.addChatMessage);

  const [chatsLoading, setChatsLoading] = useState(true);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [creatingChat, setCreatingChat] = useState(false);
  const [question, setQuestion] = useState("");
  const [asking, setAsking] = useState(false);
  const [error, setError] = useState(null);

  // Load (or bootstrap) the chat list for this session on first mount.
  useEffect(() => {
    let cancelled = false;

    async function init() {
      setChatsLoading(true);
      setError(null);
      try {
        const response = await listChats(sessionId);
        if (cancelled) return;

        if (response.chats.length === 0) {
          const chat = await createChat(sessionId);
          if (cancelled) return;
          setChats([chat]);
          setActiveChatId(chat.chat_id);
          setChatMessages(chat.chat_id, []);
        } else {
          setChats(response.chats);
          const currentActive = useSessionStore.getState().activeChatId;
          const stillValid = response.chats.some((c) => c.chat_id === currentActive);
          setActiveChatId(stillValid ? currentActive : response.chats[0].chat_id);
        }
      } catch (err) {
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setChatsLoading(false);
      }
    }

    init();
    return () => {
      cancelled = true;
    };
  }, [sessionId, setChats, setActiveChatId, setChatMessages]);

  // Fetch full history for a chat the first time it becomes active.
  useEffect(() => {
    if (!activeChatId || chatMessages[activeChatId] !== undefined) return;

    let cancelled = false;

    async function loadHistory() {
      setHistoryLoading(true);
      setError(null);
      try {
        const response = await getChatHistory(activeChatId);
        if (cancelled) return;
        setChatMessages(activeChatId, (response.messages || []).map(toEntry));
      } catch (err) {
        if (!cancelled) setError(err.message);
      } finally {
        if (!cancelled) setHistoryLoading(false);
      }
    }

    loadHistory();
    return () => {
      cancelled = true;
    };
  }, [activeChatId, chatMessages, setChatMessages]);

  async function handleNewChat() {
    setError(null);

    // Reuse an already-empty chat instead of piling up throwaway ones.
    const existingEmpty = chats.find((c) => chatMessages[c.chat_id]?.length === 0);
    if (existingEmpty) {
      setActiveChatId(existingEmpty.chat_id);
      return;
    }

    setCreatingChat(true);
    try {
      const chat = await createChat(sessionId);
      addChat(chat);
      setActiveChatId(chat.chat_id);
      setChatMessages(chat.chat_id, []);
    } catch (err) {
      setError(err.message);
    } finally {
      setCreatingChat(false);
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!question.trim() || !activeChatId) return;

    setError(null);
    setAsking(true);

    try {
      const response = await askQuestion(sessionId, activeChatId, question);
      addChatMessage(activeChatId, toEntry(response));
      setQuestion("");
    } catch (err) {
      setError(err.message);
    } finally {
      setAsking(false);
    }
  }

  const activeMessages = (activeChatId && chatMessages[activeChatId]) || [];

  return (
    <div
      style={{
        marginLeft: "calc(50% - 50vw)",
        marginRight: "calc(50% - 50vw)",
        padding: "0 24px",
      }}
    >
      <div style={{ maxWidth: 1180, margin: "0 auto", display: "flex", gap: 24, alignItems: "flex-start" }}>
        <aside style={{ width: 220, flexShrink: 0 }}>
          <button
            onClick={handleNewChat}
            disabled={creatingChat || !sessionId}
            style={{
              width: "100%",
              padding: "8px 12px",
              marginBottom: 12,
              borderRadius: "var(--radius)",
              border: "1px solid var(--color-border)",
              background: "var(--color-surface)",
              color: "var(--color-ink)",
              fontSize: 13,
              fontWeight: 600,
              opacity: creatingChat ? 0.6 : 1,
            }}
          >
            + New chat
          </button>

          {chatsLoading && (
            <div style={{ fontSize: 13, color: "var(--color-muted)" }}>Loading chats...</div>
          )}

          {!chatsLoading && chats.length === 0 && (
            <div style={{ fontSize: 13, color: "var(--color-muted)" }}>No chats yet.</div>
          )}

          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            {chats.map((chat) => {
              const isActive = chat.chat_id === activeChatId;
              return (
                <button
                  key={chat.chat_id}
                  onClick={() => setActiveChatId(chat.chat_id)}
                  style={{
                    textAlign: "left",
                    padding: "8px 12px",
                    borderRadius: "var(--radius)",
                    border: isActive ? "1px solid var(--color-accent)" : "1px solid var(--color-border)",
                    background: isActive ? "var(--color-surface)" : "transparent",
                    color: "var(--color-ink)",
                    fontSize: 13,
                    fontWeight: isActive ? 600 : 400,
                    whiteSpace: "nowrap",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                  }}
                >
                  {chat.title}
                </button>
              );
            })}
          </div>
        </aside>

        <div style={{ flex: 1, minWidth: 0 }}>
          <h1 style={{ fontSize: 22, marginBottom: 4 }}>Ask a question</h1>
          <p style={{ color: "var(--color-muted)", marginBottom: 24 }}>
            Ask anything about the connected data.
          </p>

          <div style={{ display: "flex", flexDirection: "column", gap: 24, marginBottom: 24 }}>
            {historyLoading && (
              <div style={{ color: "var(--color-muted)", fontSize: 14 }}>Loading chat history...</div>
            )}
            {!historyLoading &&
              activeMessages.map((entry, i) => <ChatEntry key={i} entry={entry} />)}
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
              disabled={asking || !activeChatId}
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
              disabled={asking || !activeChatId}
              style={{
                padding: "10px 20px",
                borderRadius: "var(--radius)",
                border: "none",
                background: "var(--color-accent)",
                color: "white",
                fontSize: 14,
                fontWeight: 600,
                opacity: asking || !activeChatId ? 0.6 : 1,
              }}
            >
              {asking ? "Thinking..." : "Ask"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

function ChatEntry({ entry }) {
  const [activeTab, setActiveTab] = useState("answer");
  const [selectedChartId, setSelectedChartId] = useState(entry.selectedChartId);

  const selectedCandidate = entry.chartCandidates.find((c) => c.chart_id === selectedChartId);
  const isSingleValueResult =
    entry.chartCandidates.length === 0 &&
    entry.resultRows &&
    entry.resultRows.length === 1 &&
    Object.keys(entry.resultRows[0]).length > 0;

  const TABS = [
    { key: "answer", label: "Answer" },
    { key: "query", label: "Query" },
    { key: "table", label: "Table" },
    ...(entry.chartCandidates.length > 0 || isSingleValueResult ? [{ key: "chart", label: "Chart" }] : []),
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
            {!selectedCandidate && isSingleValueResult && (
              <KpiCard rows={entry.resultRows} />
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
