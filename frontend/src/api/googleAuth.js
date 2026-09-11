// frontend/src/api/googleAuth.js

import { get } from "./client";

export async function getGoogleLoginUrl() {
  return get("/auth/google/login");
}

export async function searchGoogleSheets(googleSessionId, query) {
  return get(`/auth/google/sheets?google_session_id=${googleSessionId}&query=${encodeURIComponent(query)}`);
}