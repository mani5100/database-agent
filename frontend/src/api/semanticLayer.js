// frontend/src/api/semanticLayer.js

import { post } from "./client";

export async function generateTableNames(sessionId) {
  return post(`/session/${sessionId}/generate_table_names`);
}

export async function generateTableDetails(sessionId, tableName) {
  return post(`/session/${sessionId}/generate_table_details/${tableName}`);
}

export async function assembleSemanticLayer(sessionId, selectedTables) {
  return post(`/session/${sessionId}/assemble_semantic_layer`, {
    selected_tables: selectedTables,
  });
}