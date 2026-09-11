// frontend/src/store/sessionStore.js

import { create } from "zustand";

export const useSessionStore = create((set) => ({
  // Wizard progress
  currentStep: "connect", // "connect" | "select" | "review" | "ask"

  // Connection state
  sessionId: null,
  sourceType: null,

  googleSessionId: null,

  // Phase 1: table names
  tableNames: {}, // { physical_name: business_name }

  // User's table selection
  selectedTables: [], // [physical_name, ...]

  // Phase 2: per-table details, keyed by physical_name, for progress display
  tableDetails: {}, // { physical_name: { description, synonyms, columns } }

  // Assembly result
  semanticLayerFilePath: null,
  indexedPoints: null,

  // Chats for the ask page — multiple independent conversations per session
  chats: [], // [{ chat_id, title }, ...]
  activeChatId: null,
  chatMessages: {}, // { [chat_id]: [{ question, sql, answer, resultRows, chartCandidates, selectedChartId }, ...] }

  // --- actions ---

  setConnection: (sessionId, sourceType) =>
    set({ sessionId, sourceType, currentStep: "select" }),

  setGoogleSessionId: (googleSessionId) => set({ googleSessionId }),

  setActiveSession: (sessionId, sourceType) =>
    set({
      sessionId,
      sourceType,
      tableNames: {},
      selectedTables: [],
      tableDetails: {},
      semanticLayerFilePath: null,
      indexedPoints: null,
      chats: [],
      activeChatId: null,
      chatMessages: {},
    }),
    
  setTableNames: (tableNames) => set({ tableNames }),

  toggleTableSelection: (physicalName) =>
    set((state) => {
      const isSelected = state.selectedTables.includes(physicalName);
      return {
        selectedTables: isSelected
          ? state.selectedTables.filter((t) => t !== physicalName)
          : [...state.selectedTables, physicalName],
      };
    }),

  setTableDetail: (physicalName, detail) =>
    set((state) => ({
      tableDetails: { ...state.tableDetails, [physicalName]: detail },
    })),

  setAssemblyResult: (filePath, indexedPoints) =>
    set({
      semanticLayerFilePath: filePath,
      indexedPoints,
      currentStep: "review",
    }),

  setChats: (chats) => set({ chats }),

  addChat: (chat) =>
    set((state) => ({ chats: [...state.chats, chat] })),

  setActiveChatId: (chatId) => set({ activeChatId: chatId }),

  setChatMessages: (chatId, messages) =>
    set((state) => ({
      chatMessages: { ...state.chatMessages, [chatId]: messages },
    })),

  addChatMessage: (chatId, entry) =>
    set((state) => ({
      chatMessages: {
        ...state.chatMessages,
        [chatId]: [...(state.chatMessages[chatId] || []), entry],
      },
    })),

  goToStep: (step) => set({ currentStep: step }),

  reset: () =>
    set({
      currentStep: "connect",
      sessionId: null,
      sourceType: null,
      tableNames: {},
      selectedTables: [],
      tableDetails: {},
      semanticLayerFilePath: null,
      indexedPoints: null,
      chats: [],
      activeChatId: null,
      chatMessages: {},
    }),
}));