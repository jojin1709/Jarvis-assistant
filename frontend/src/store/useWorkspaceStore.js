import { create } from "zustand";
import { persist } from "zustand/middleware";

const initialSettings = {
  theme: "dark",
  aiProvider: "local-env",
  startupAudio: true,
  wakeWord: true,
  voiceLanguage: "auto",
};

function randomId() {
  return globalThis.crypto?.randomUUID?.() || `chat-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function chatTitleFrom(messages) {
  const firstUserMessage = messages.find((item) => String(item?.transcript || "").trim());
  const title = String(firstUserMessage?.transcript || "New chat").replace(/\s+/g, " ").trim();
  return title.length > 52 ? `${title.slice(0, 49)}...` : title;
}

function isCleanConversation(item) {
  const transcript = String(item?.transcript || "").trim().toLowerCase();
  const response = String(item?.response || "").trim().toLowerCase();
  return (
    transcript !== "startup greeting" &&
    !response.startsWith("blocked") &&
    !response.startsWith("confirmation required") &&
    !response.startsWith("approval requested")
  );
}

function cleanConversations(items = []) {
  return Array.isArray(items) ? items.filter(isCleanConversation).slice(0, 80) : [];
}

function makeChatThread(messages = []) {
  const cleanedMessages = cleanConversations(messages);
  const now = new Date().toISOString();
  return {
    id: randomId(),
    title: chatTitleFrom(cleanedMessages),
    createdAt: cleanedMessages.at(-1)?.createdAt || now,
    updatedAt: cleanedMessages[0]?.createdAt || now,
    messages: cleanedMessages,
  };
}

function ensureActiveThread(state) {
  const activeThread = state.chatThreads.find((thread) => thread.id === state.activeChatId);
  if (activeThread) return { activeChatId: activeThread.id, chatThreads: state.chatThreads };

  const thread = makeChatThread(state.chatHistory);
  return {
    activeChatId: thread.id,
    chatThreads: [thread, ...state.chatThreads],
  };
}

export const useWorkspaceStore = create(
  persist(
    (set, get) => ({
      activePage: "home",
      backendOnline: false,
      mode: "online",
      userName: "User",
      wakeEnabled: true,
      languageMode: "auto",
      transcript: "Awaiting command.",
      response: "Jarvis is ready. Ask for an action or start a conversation.",
      activeChatId: null,
      chatThreads: [],
      chatHistory: [],
      voiceHistory: [],
      uploads: [],
      tasks: [],
      installedApps: [],
      executionLogs: [],
      thinkingTimeline: [],
      executionControl: { paused: false, cancelled: false },
      permissions: null,
      permissionActivity: [],
      profile: null,
      memoryStorage: null,
      contextSnapshot: null,
      workflowRecorder: { active: false, current: null, lastSaved: null, workflows: [] },
      plugins: [],
      aiProviders: [],
      aiProviderConfig: null,
      ollamaModels: [],
      providerOrchestration: { providers: [], history: [], events: [], config: {} },
      autonomousDashboard: { context: {}, telemetry: {}, agents: {}, workflows: {} },
      voiceRuntime: { enabled: true, status: "idle", mode: "push_to_talk", muted: false, hotkey: "Space+M", preferences: {} },
      vision: null,
      browserState: { status: "idle", currentAction: "Ready", logs: [], history: [], domSummary: { inputs: [], buttons: [], links: [] }, tabs: [] },
      memory: { interests: [], memory_count: 0, saved_name: null, user_name: "User" },
      notifications: [],
      settings: initialSettings,
      commandPaletteOpen: false,

      setActivePage: (page) => set({ activePage: page }),
      setBackendOnline: (backendOnline) => set({ backendOnline }),
      setMode: (mode) => set({ mode }),
      setUserName: (userName) => set({ userName }),
      setWakeEnabled: (wakeEnabled) => set({ wakeEnabled, settings: { ...get().settings, wakeWord: wakeEnabled } }),
      setLanguageMode: (languageMode) => set({ languageMode, settings: { ...get().settings, voiceLanguage: languageMode } }),
      setTranscript: (transcript) => set({ transcript }),
      setResponse: (response) => set({ response }),
      setMemory: (memory) => set({ memory, userName: memory?.user_name || get().userName }),
      setInstalledApps: (installedApps) => set({ installedApps }),
      setPermissions: (permissions) => set({ permissions }),
      setPermissionActivity: (permissionActivity) => set({ permissionActivity }),
      setProfile: (profile) => set({ profile, userName: profile?.user_name || get().userName }),
      setMemoryStorage: (memoryStorage) => set({ memoryStorage }),
      setBrowserState: (browserState) => set({ browserState }),
      setThinkingTimeline: (thinkingTimeline, executionControl = get().executionControl) => set({ thinkingTimeline, executionControl }),
      setContextSnapshot: (contextSnapshot) => set({ contextSnapshot }),
      setWorkflowRecorder: (workflowRecorder) => set({ workflowRecorder }),
      setPlugins: (plugins) => set({ plugins }),
      setAiProviders: (aiProviders, aiProviderConfig = get().aiProviderConfig, ollamaModels = get().ollamaModels) =>
        set({ aiProviders, aiProviderConfig, ollamaModels }),
      setProviderOrchestration: (providerOrchestration) => set({ providerOrchestration }),
      setAutonomousDashboard: (autonomousDashboard) => set({ autonomousDashboard }),
      setVoiceRuntime: (voiceRuntime) => set({ voiceRuntime }),
      setVision: (vision) => set({ vision }),
      setCommandPaletteOpen: (commandPaletteOpen) => set({ commandPaletteOpen }),
      updateSettings: (patch) => set({ settings: { ...get().settings, ...patch } }),

      addConversation: (item) => {
        if (!isCleanConversation(item)) return null;
        const entry = { id: randomId(), createdAt: new Date().toISOString(), ...item };
        set((state) => {
          const active = ensureActiveThread(state);
          const chatHistory = [entry, ...cleanConversations(state.chatHistory)].slice(0, 80);
          const chatThreads = active.chatThreads
            .map((thread) => {
              if (thread.id !== active.activeChatId) return thread;
              const messages = [entry, ...cleanConversations(thread.messages)].slice(0, 80);
              return {
                ...thread,
                title: chatTitleFrom(messages),
                updatedAt: entry.createdAt,
                messages,
              };
            })
            .sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime());
          return {
            activeChatId: active.activeChatId,
            chatHistory,
            chatThreads,
          };
        });
        return entry.id;
      },
      updateConversation: (id, patch) =>
        set((state) => {
          const activeHistoryContainsItem = state.chatHistory.some((item) => item.id === id);
          const chatThreads = state.chatThreads
            .map((thread) => {
              if (!thread.messages?.some((item) => item.id === id)) return thread;
              const messages = cleanConversations(thread.messages.map((item) => (item.id === id ? { ...item, ...patch } : item)));
              return {
                ...thread,
                title: chatTitleFrom(messages),
                updatedAt: messages[0]?.createdAt || thread.updatedAt,
                messages,
              };
            })
            .sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime());
          return {
            chatHistory: activeHistoryContainsItem
              ? cleanConversations(state.chatHistory.map((item) => (item.id === id ? { ...item, ...patch } : item)))
              : state.chatHistory,
            chatThreads,
          };
        }),
      startNewChat: () =>
        set((state) => {
          if (!state.chatHistory.length && state.activeChatId) return state;
          const thread = makeChatThread([]);
          return {
            activeChatId: thread.id,
            chatHistory: [],
            chatThreads: [thread, ...state.chatThreads.filter((item) => item.messages?.length)].slice(0, 30),
          };
        }),
      selectChatThread: (id) =>
        set((state) => {
          const thread = state.chatThreads.find((item) => item.id === id);
          if (!thread) return state;
          return {
            activeChatId: thread.id,
            chatHistory: cleanConversations(thread.messages),
            chatThreads: state.chatThreads.filter((item) => item.id === thread.id || item.messages?.length),
          };
        }),
      addVoiceHistory: (item) =>
        set((state) => ({
          voiceHistory: [{ id: randomId(), createdAt: new Date().toISOString(), ...item }, ...state.voiceHistory].slice(0, 80),
        })),
      addUpload: (upload) => set((state) => ({ uploads: [upload, ...state.uploads].slice(0, 24) })),
      addTask: (task) =>
        set((state) => ({
          tasks: [{ id: randomId(), createdAt: new Date().toISOString(), status: "running", ...task }, ...state.tasks].slice(0, 40),
        })),
      updateTask: (id, patch) =>
        set((state) => ({ tasks: state.tasks.map((task) => (task.id === id ? { ...task, ...patch } : task)) })),
      addExecutionLog: (log) =>
        set((state) => ({
          executionLogs: [{ id: randomId(), createdAt: new Date().toISOString(), level: "info", ...log }, ...state.executionLogs].slice(0, 120),
        })),
      setExecutionLogs: (logs) => set({ executionLogs: logs }),
      clearChatHistory: () =>
        set((state) => ({
          chatHistory: [],
          chatThreads: state.chatThreads
            .map((thread) => (thread.id === state.activeChatId ? { ...thread, title: "New chat", messages: [] } : thread))
            .filter((thread) => thread.id === state.activeChatId || thread.messages?.length),
        })),
      clearVoiceHistory: () => set({ voiceHistory: [] }),
      addNotification: (notification) =>
        set((state) => ({
          notifications: [{ id: randomId(), createdAt: new Date().toISOString(), ...notification }, ...state.notifications].slice(0, 30),
        })),
      clearExecutionLogs: () => set({ executionLogs: [] }),
    }),
    {
      name: "jx-jarvis-workspace",
      version: 3,
      migrate: (state) => {
        const chatHistory = cleanConversations(state?.chatHistory);
        const chatThreads = Array.isArray(state?.chatThreads)
          ? state.chatThreads
              .map((thread) => ({ ...thread, messages: cleanConversations(thread.messages) }))
              .filter((thread) => thread.messages.length)
          : [];
        const fallbackThread = chatHistory.length ? makeChatThread(chatHistory) : null;
        const nextThreads = chatThreads.length ? chatThreads : fallbackThread ? [fallbackThread] : [];
        return {
          ...state,
          activeChatId: state?.activeChatId || nextThreads[0]?.id || null,
          chatThreads: nextThreads,
          chatHistory: nextThreads.find((thread) => thread.id === (state?.activeChatId || nextThreads[0]?.id))?.messages || chatHistory,
        };
      },
      partialize: (state) => ({
        activePage: state.activePage,
        languageMode: state.languageMode,
        wakeEnabled: state.wakeEnabled,
        activeChatId: state.activeChatId,
        chatThreads: state.chatThreads
          .map((thread) => ({ ...thread, messages: cleanConversations(thread.messages).slice(0, 30) }))
          .filter((thread) => thread.id === state.activeChatId || thread.messages.length)
          .slice(0, 30),
        chatHistory: cleanConversations(state.chatHistory).slice(0, 30),
        voiceHistory: state.voiceHistory.slice(0, 30),
        settings: state.settings,
      }),
    },
  ),
);
