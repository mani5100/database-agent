// frontend/src/api/chats.js

import { get, post } from "./client";

export async function createChat(sessionId, title = "New chat") {
  return post(`/session/${sessionId}/chats`, { title });
}

export async function listChats(sessionId) {
  return get(`/session/${sessionId}/chats`);
}

export async function getChatHistory(chatId) {
  return get(`/chats/${chatId}/history`);
}
