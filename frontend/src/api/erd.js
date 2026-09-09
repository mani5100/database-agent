// frontend/src/api/erd.js

import { get } from "./client";

export async function getErd(sessionId) {
  return get(`/session/${sessionId}/erd`);
}