const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8004/api/v1";

function getHeaders() {
  const token = localStorage.getItem("dev_token");
  const headers = { "Content-Type": "application/json" };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

async function handleResponse(response) {
  const isJson = response.headers.get("content-type")?.includes("application/json");
  const data = isJson ? await response.json() : null;

  if (!response.ok) {
    const error = (data && data.error && data.error.message) || response.statusText;
    return Promise.reject(error);
  }

  return data;
}

export const api = {
  get: (endpoint) =>
    fetch(`${API_BASE}${endpoint}`, {
      method: "GET",
      headers: getHeaders(),
    }).then(handleResponse),

  post: (endpoint, body) =>
    fetch(`${API_BASE}${endpoint}`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify(body),
    }).then(handleResponse),

  patch: (endpoint, body) =>
    fetch(`${API_BASE}${endpoint}`, {
      method: "PATCH",
      headers: getHeaders(),
      body: JSON.stringify(body),
    }).then(handleResponse),
};
