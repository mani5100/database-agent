// frontend/src/api/agent.js

import { post } from "./client";

export async function askQuestion(sessionId, question) {
  return post(`/session/${sessionId}/ask`, { question });
}