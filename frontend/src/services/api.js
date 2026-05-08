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

export function executeAgentTask(text) {
  return request("/api/agent/execute", {
    method: "POST",
    body: JSON.stringify({ text }),
  });
}

export function previewAgentPlan(text) {
  return request("/api/agent/plan", {
    method: "POST",
    body: JSON.stringify({ text }),
  });
}

export function pauseAgentTask() {
  return request("/api/agent/pause", { method: "POST" });
}

export function resumeAgentTask() {
  return request("/api/agent/resume", { method: "POST" });
}

export function cancelAgentTask() {
  return request("/api/agent/cancel", { method: "POST" });
}

export function getExecutionLogs() {
  return request("/api/agent/logs");
}

export function getThinkingTimeline() {
  return request("/api/agent/thinking");
}

export function getContextSnapshot() {
  return request("/api/context");
}

export function captureVisionScreenshot() {
  return request("/api/vision/screenshot", { method: "POST" });
}

export function getWorkflowRecorder() {
  return request("/api/workflows/recorder");
}

export function startWorkflowRecording(name) {
  return request("/api/workflows/recorder/start", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
}

export function stopWorkflowRecording() {
  return request("/api/workflows/recorder/stop", { method: "POST" });
}

export function replayWorkflow(id) {
  return request(`/api/workflows/replay/${encodeURIComponent(id)}`, { method: "POST" });
}

export function getPlugins() {
  return request("/api/plugins");
}

export function getProviders() {
  return request("/api/providers");
}

export function updateProviderConfig(patch) {
  return request("/api/providers/config", {
    method: "PATCH",
    body: JSON.stringify(patch),
  });
}

export function saveProviderKey(provider, apiKey) {
  return request("/api/providers/key", {
    method: "POST",
    body: JSON.stringify({ provider, apiKey }),
  });
}

export function removeProviderKey(provider) {
  return request(`/api/providers/key/${encodeURIComponent(provider)}`, { method: "DELETE" });
}

export function testProvider(provider, model) {
  return request("/api/providers/test", {
    method: "POST",
    body: JSON.stringify({ provider, model }),
  });
}

export function getOllamaModels() {
  return request("/api/providers/ollama/models");
}

export function analyzeCodingProject(path) {
  const query = path ? `?path=${encodeURIComponent(path)}` : "";
  return request(`/api/coding/analyze${query}`);
}

export function runCodingScript(path, script = "build") {
  return request("/api/coding/run-script", {
    method: "POST",
    body: JSON.stringify({ path, script }),
  });
}

export function getMemory() {
  return request("/api/memory");
}

export function getProfile() {
  return request("/api/profile");
}

export function updateProfile(patch) {
  return request("/api/profile", {
    method: "PATCH",
    body: JSON.stringify(patch),
  });
}

export function completeOnboarding(payload) {
  return request("/api/onboarding/complete", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function clearMemory() {
  return request("/api/memory/clear", { method: "POST" });
}

export function getMemoryStorage() {
  return request("/api/memory/storage");
}

export function setupMemoryStorage(path) {
  return request("/api/memory/storage/setup", {
    method: "POST",
    body: JSON.stringify({ path }),
  });
}

export function backupMemoryStorage() {
  return request("/api/memory/storage/backup", { method: "POST" });
}

export function clearBrainMemory() {
  return request("/api/memory/storage/clear", { method: "POST" });
}

export function exportMemory() {
  return request("/api/memory/export");
}

export function getSystemApps() {
  return request("/api/system/apps");
}

export function getPermissions() {
  return request("/api/security/permissions");
}

export function updatePermissions(patch) {
  return request("/api/security/permissions", {
    method: "PATCH",
    body: JSON.stringify(patch),
  });
}

export function getPermissionActivity() {
  return request("/api/security/activity");
}

export function getBrowserState() {
  return request("/api/browser/state");
}

export function runBrowserTask(text) {
  return request("/api/browser/run", {
    method: "POST",
    body: JSON.stringify({ text }),
  });
}

export function pauseBrowserTask() {
  return request("/api/browser/pause", { method: "POST" });
}

export function resumeBrowserTask() {
  return request("/api/browser/resume", { method: "POST" });
}

export function stopBrowserTask() {
  return request("/api/browser/stop", { method: "POST" });
}

export function closeBrowserTask() {
  return request("/api/browser/close", { method: "POST" });
}

export { API_BASE };
