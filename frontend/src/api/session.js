// frontend/src/api/session.js

import { get } from "./client";

export async function listSessions() {
  return get("/sessions");
}