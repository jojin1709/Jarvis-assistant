const API_BASE = import.meta.env.VITE_BACKEND_URL || "http://127.0.0.1:8765";

async function request(path, options = {}) {
  const isFormData = options.body instanceof FormData;
  const response = await fetch(`${API_BASE}${path}`, {
    headers: isFormData
      ? options.headers || {}
      : {
          "Content-Type": "application/json",
          ...(options.headers || {}),
        },
    ...options,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with status ${response.status}`);
  }

  return response.json();
}

export function health() {
  return request("/api/health");
}

export function getStatus() {
  return request("/api/status");
}

export function listenCommand(language = "auto") {
  return request("/api/assistant/listen", {
    method: "POST",
    body: JSON.stringify({ language }),
  });
}

export function wakeListen(duration = 3.2, language = "auto") {
  return request("/api/assistant/wake-listen", {
    method: "POST",
    body: JSON.stringify({ duration, language }),
  });
}

export function greetCommand() {
  return request("/api/assistant/greet", { method: "POST" });
}

export function chatCommand(text, speak = true, language = "auto") {
  return request("/api/assistant/chat", {
    method: "POST",
    body: JSON.stringify({ text, speak, language }),
  });
}

export function runSystemTask(task) {
  return request("/api/system/task", {
    method: "POST",
    body: JSON.stringify({ task }),
  });
}

export function uploadFile(file) {
  const body = new FormData();
  body.append("file", file);
  return request("/api/files/upload", {
    method: "POST",
    body,
  });
}
