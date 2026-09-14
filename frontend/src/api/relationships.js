// frontend/src/api/relationships.js

import { del, get, post, put } from "./client";

export async function getRelationships(sessionId) {
  return get(`/session/${sessionId}/relationships`);
}

export async function createRelationship(sessionId, relationship) {
  return post(`/session/${sessionId}/relationships`, relationship);
}

export async function updateRelationship(sessionId, relationshipName, relationship) {
  return put(`/session/${sessionId}/relationships/${relationshipName}`, relationship);
}

export async function deleteRelationship(sessionId, relationshipName) {
  return del(`/session/${sessionId}/relationships/${relationshipName}`);
}
