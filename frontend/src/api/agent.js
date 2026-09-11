// frontend/src/api/agent.js

import { post } from "./client";

export async function askQuestion(sessionId, chatId, question) {
  return post(`/session/${sessionId}/ask`, { chat_id: chatId, question });
}