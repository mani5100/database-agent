// frontend/src/api/connections.js

import { get, post, postFormData, del } from "./client";

export async function connectPostgres({ host, port, user, password, database, schema }) {
  return post("/connect/postgres", { host, port, user, password, database, schema });
}

export async function connectMysql({ host, port, user, password, database }) {
  return post("/connect/mysql", { host, port, user, password, database });
}

export async function connectCsv(file) {
  const formData = new FormData();
  formData.append("file", file);
  return postFormData("/connect/csv", formData);
}

export async function connectExcel(file) {
  const formData = new FormData();
  formData.append("file", file);
  return postFormData("/connect/excel", formData);
}

export async function getSessionSchema(sessionId) {
  return get(`/session/${sessionId}/schema`);
}

export async function closeSession(sessionId) {
  return del(`/session/${sessionId}`);
}