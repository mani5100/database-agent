// frontend/src/api/erd.js

import { get, put } from "./client";

export async function getErd(sessionId) {
  return get(`/session/${sessionId}/erd`);
}

export async function updateEntity(sessionId, physicalTableName, payload) {
  return put(`/session/${sessionId}/entities/${physicalTableName}`, payload);
}