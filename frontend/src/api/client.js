// frontend/src/api/client.js

const API_BASE_URL = "http://localhost:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const message = body.detail || `Request failed with status ${response.status}`;
    throw new Error(message);
  }

  return response.json();
}

export async function get(path) {
  return request(path, { method: "GET" });
}

export async function post(path, body) {
  return request(path, {
    method: "POST",
    body: body ? JSON.stringify(body) : undefined,
  });
}

export async function postFormData(path, formData) {
  return request(path, {
    method: "POST",
    headers: {}, // let the browser set the multipart Content-Type + boundary
    body: formData,
  });
}

export async function put(path, body) {
  return request(path, {
    method: "PUT",
    body: body ? JSON.stringify(body) : undefined,
  });
}

export async function del(path) {
  return request(path, { method: "DELETE" });
}