import { create } from "zustand";
import { persist } from "zustand/middleware";

const initialSettings = {
  theme: "dark",
  aiProvider: "local-env",
  startupAudio: true,
  wakeWord: true,
  voiceLanguage: "auto",
};

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
      setVision: (vision) => set({ vision }),
      setCommandPaletteOpen: (commandPaletteOpen) => set({ commandPaletteOpen }),
      updateSettings: (patch) => set({ settings: { ...get().settings, ...patch } }),

      addConversation: (item) =>
        set((state) => ({
          chatHistory: [{ id: crypto.randomUUID(), createdAt: new Date().toISOString(), ...item }, ...state.chatHistory].slice(0, 80),
        })),
      addVoiceHistory: (item) =>
        set((state) => ({
          voiceHistory: [{ id: crypto.randomUUID(), createdAt: new Date().toISOString(), ...item }, ...state.voiceHistory].slice(0, 80),
        })),
      addUpload: (upload) => set((state) => ({ uploads: [upload, ...state.uploads].slice(0, 24) })),
      addTask: (task) =>
        set((state) => ({
          tasks: [{ id: crypto.randomUUID(), createdAt: new Date().toISOString(), status: "running", ...task }, ...state.tasks].slice(0, 40),
        })),
      updateTask: (id, patch) =>
        set((state) => ({ tasks: state.tasks.map((task) => (task.id === id ? { ...task, ...patch } : task)) })),
      addExecutionLog: (log) =>
        set((state) => ({
          executionLogs: [{ id: crypto.randomUUID(), createdAt: new Date().toISOString(), level: "info", ...log }, ...state.executionLogs].slice(0, 120),
        })),
      setExecutionLogs: (logs) => set({ executionLogs: logs }),
      addNotification: (notification) =>
        set((state) => ({
          notifications: [{ id: crypto.randomUUID(), createdAt: new Date().toISOString(), ...notification }, ...state.notifications].slice(0, 30),
        })),
      clearExecutionLogs: () => set({ executionLogs: [] }),
    }),
    {
      name: "jx-jarvis-workspace",
      partialize: (state) => ({
        activePage: state.activePage,
        languageMode: state.languageMode,
        wakeEnabled: state.wakeEnabled,
        chatHistory: state.chatHistory.slice(0, 30),
        voiceHistory: state.voiceHistory.slice(0, 30),
        settings: state.settings,
      }),
    },
  ),
);
