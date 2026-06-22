import { useEffect, useMemo, useRef } from "react";

import {
  chatCommand,
  cancelAgentTask,
  captureVisionScreenshot,
  closeBrowserTask,
  executeAgentTask,
  getAutonomousDashboard,
  getBrowserState,
  getContextSnapshot,
  getExecutionLogs,
  getMemory,
  getMemoryStorage,
  getPermissionActivity,
  getPermissions,
  getPlugins,
  getProviders,
  getProviderOrchestration,
  getProfile,
  getSystemApps,
  getThinkingTimeline,
  getVoiceRuntime,
  getWorkflowRecorder,
  greetCommand,
  health,
  listenCommand,
  pauseAgentTask,
  previewAgentPlan,
  pauseBrowserTask,
  replayWorkflow,
  resumeAgentTask,
  resumeBrowserTask,
  runBrowserTask,
  runSystemTask,
  startWorkflowRecording,
  stopBrowserTask,
  stopWorkflowRecording,
  streamChatCommand,
  uploadFile,
  wakeListen,
  updateVoiceRuntime,
} from "../services/api.js";
import { useWorkspaceStore } from "../store/useWorkspaceStore.js";
import { fx } from "../lib/sounds.js";
import { setElectronVoiceRuntime, subscribeToGlobalVoice, triggerGlobalPushToTalk } from "../voice/hotkey_listener.ts";

const wait = (milliseconds) => new Promise((resolve) => window.setTimeout(resolve, milliseconds));
const googlePrefixPattern = /^(?:gg|\/g)\s+/i;

function googleSearchCommand(text) {
  const query = text.replace(googlePrefixPattern, "").trim();
  return query ? `search google for ${query}` : text;
}

export function useJarvisRuntime() {
  const store = useWorkspaceStore();
  const greetingStarted = useRef(false);
  const wakeLoopActive = useRef(false);
  const modeRef = useRef(store.mode);
  const languageModeRef = useRef(store.languageMode);
  const textCommandInFlight = useRef(false);
  const lastTextCommand = useRef({ text: "", startedAt: 0 });

  const busy = useMemo(
    () => ["listening", "thinking", "speaking", "executing", "indexing", "coding", "memory"].includes(store.mode),
    [store.mode],
  );
  const activeWave = useMemo(() => busy || store.mode === "online" || store.mode === "wake", [busy, store.mode]);

  useEffect(() => {
    modeRef.current = store.mode;
  }, [store.mode]);

  useEffect(() => {
    languageModeRef.current = store.languageMode;
  }, [store.languageMode]);

  useEffect(() => {
    const check = async () => {
      try {
        const result = await health();
        store.setBackendOnline(true);
        store.setMemory(result.profile || {});
        store.setUserName(result.profile?.user_name || "User");
        if (!greetingStarted.current && !window.sessionStorage.getItem("jxJarvisGreeted")) {
          greetingStarted.current = true;
          store.setMode("speaking");
          store.setTranscript("Startup greeting");
          store.setResponse("Preparing workspace...");
          try {
            const greeting = await greetCommand();
            window.sessionStorage.setItem("jxJarvisGreeted", "true");
            store.setTranscript(greeting.transcript);
            store.setResponse(greeting.response);
            store.addConversation({ transcript: greeting.transcript, response: greeting.response });
            store.setMode("online");
          } catch {
            greetingStarted.current = false;
            store.setMode("online");
            store.setResponse("Backend is online. Greeting will retry shortly.");
          }
        }
      } catch {
        store.setBackendOnline(false);
      }
    };

    check();
    const poll = window.setInterval(check, 3500);
    return () => window.clearInterval(poll);
  }, []);

  useEffect(() => {
    const poll = async () => {
      if (!store.backendOnline) return;
      try {
        const [logs, memory, memoryStorage, apps, permissions, permissionActivity, browserState, profile] = await Promise.all([
          getExecutionLogs(),
          getMemory(),
          getMemoryStorage(),
          getSystemApps(),
          getPermissions(),
          getPermissionActivity(),
          getBrowserState(),
          getProfile(),
        ]);
        store.setExecutionLogs(logs.logs || []);
        store.setMemory(memory.profile || memory);
        store.setMemoryStorage(memoryStorage.memory || null);
        store.setInstalledApps(apps.apps || []);
        store.setPermissions(permissions.permissions || null);
        store.setPermissionActivity(permissionActivity.activity || []);
        store.setBrowserState(browserState || {});
        store.setProfile(profile.profile || null);
      } catch {
        // Background telemetry should not interrupt the workspace.
      }
    };

    poll();
    const timer = window.setInterval(poll, 3000);
    return () => window.clearInterval(timer);
  }, [store.backendOnline]);

  useEffect(() => {
    if (!store.backendOnline) return undefined;
    const poll = async () => {
      try {
        const result = await getVoiceRuntime();
        store.setVoiceRuntime(result.runtime || {});
      } catch {
        // Voice runtime starts with the backend; status polling is best-effort.
      }
    };
    poll();
    const timer = window.setInterval(poll, 2500);
    return () => window.clearInterval(timer);
  }, [store.backendOnline]);

  useEffect(() => {
    const unsubscribe = subscribeToGlobalVoice((event) => {
      if (event.type === "activation") {
        fx.listening();
        store.setMode("listening");
        store.setTranscript("Push-to-talk activated.");
        store.setResponse("Listening from global hotkey Space+M.");
        store.addExecutionLog({ message: "Global push-to-talk activated.", level: "running" });
        return;
      }
      if (event.type === "runtime") {
        store.setVoiceRuntime(event.runtime || {});
        return;
      }
      if (event.type === "complete") {
        const result = event.result || {};
        fx.response();
        store.setMode("online");
        store.setTranscript(result.transcript || "Voice command");
        store.setResponse(result.response || "Done.");
        store.addVoiceHistory({ transcript: result.transcript || "", response: result.response || "" });
        store.addConversation({ transcript: result.transcript || "Voice command", response: result.response || "Done." });
        store.addExecutionLog({ message: `Global voice command complete: ${result.transcript || "voice command"}`, level: "success" });
        return;
      }
      if (event.type === "error") {
        store.setMode("error");
        store.setResponse(event.message || "Voice hotkey failed.");
        store.addExecutionLog({ message: event.message || "Voice hotkey failed.", level: "error" });
      }
    });
    return unsubscribe;
  }, []);

  useEffect(() => {
    if (!store.backendOnline) return undefined;
    const poll = async () => {
      try {
        const [thinking, context, recorder, plugins, providers, orchestration, dashboard] = await Promise.all([
          getThinkingTimeline(),
          getContextSnapshot(),
          getWorkflowRecorder(),
          getPlugins(),
          getProviders(),
          getProviderOrchestration(),
          getAutonomousDashboard(),
        ]);
        store.setThinkingTimeline(thinking.thinking || [], thinking.control || undefined);
        store.setContextSnapshot(context.context || null);
        store.setWorkflowRecorder(recorder.recorder || {});
        store.setPlugins(plugins.plugins || []);
        store.setAiProviders(providers.providers || [], providers.config || null, providers.ollamaModels || []);
        store.setProviderOrchestration(orchestration || {});
        store.setAutonomousDashboard(dashboard || {});
      } catch {
        // Advanced telemetry is optional while subsystems are starting.
      }
    };
    poll();
    const timer = window.setInterval(poll, 3500);
    return () => window.clearInterval(timer);
  }, [store.backendOnline]);

  useEffect(() => {
    if (!store.backendOnline) return undefined;
    const timer = window.setInterval(async () => {
      try {
        const browserState = await getBrowserState();
        store.setBrowserState(browserState || {});
      } catch {
        // Browser telemetry is optional while the backend is starting.
      }
    }, store.browserState?.status === "running" || store.browserState?.status === "paused" ? 900 : 2200);
    return () => window.clearInterval(timer);
  }, [store.backendOnline, store.browserState?.status]);

  useEffect(() => {
    if (!store.wakeEnabled || !store.backendOnline) return undefined;

    let cancelled = false;

    async function runWakeLoop() {
      while (wakeLoopActive.current && !cancelled) {
        await wait(200);
      }
      if (cancelled) return;

      wakeLoopActive.current = true;

      while (!cancelled) {
        const currentMode = modeRef.current;
        if (currentMode !== "online" && currentMode !== "wake") {
          await wait(650);
          continue;
        }

        try {
          store.setMode("wake");
          const result = await wakeListen(2.8, store.languageMode);
          if (cancelled) break;

          if (result.status === "blocked") {
            store.setMode("online");
            store.setResponse(result.response || "Background listening is blocked by Security & Permissions.");
            store.addExecutionLog({ message: result.response || "Background listening blocked", level: "error" });
            await wait(3000);
            continue;
          }

          if (!result.awakened) {
            store.setMode("online");
            await wait(450);
            continue;
          }

          fx.response();
          store.addExecutionLog({ message: "Wake word detected", level: "success" });
          const heard = result.command ? `Hey Jarvis: ${result.command}` : result.transcript;
          store.setTranscript(heard);
          store.setResponse(result.response || "Listening.");

          if (result.response) {
            store.addConversation({ transcript: heard, response: result.response });
          }
          if (result.status === "complete") {
            store.addExecutionLog({ message: `Executed wake command: ${result.command || result.transcript}`, level: "success" });
          }

          if (result.status === "awake") {
            store.setMode("listening");
            store.setResponse("Listening for your command...");
            store.addExecutionLog({ message: "Listening for follow-up command", level: "running" });
            const followUp = await listenCommand(store.languageMode);
            if (cancelled) break;
            fx.response();
            store.setTranscript(followUp.transcript);
            store.setResponse(followUp.response);
            store.addExecutionLog({ message: `Executed voice command: ${followUp.transcript}`, level: "success" });
            store.addVoiceHistory({ transcript: followUp.transcript, response: followUp.response });
            store.addConversation({ transcript: followUp.transcript, response: followUp.response });
          }

          store.setMode("online");
          await wait(1200);
        } catch {
          if (!cancelled) {
            store.setMode("online");
            await wait(1400);
          }
        }
      }

      wakeLoopActive.current = false;
    }

    runWakeLoop();

    return () => {
      cancelled = true;
    };
  }, [store.backendOnline, store.wakeEnabled, store.languageMode]);

  async function runVoiceFlow() {
    const restoreWake = store.wakeEnabled;
    store.setWakeEnabled(false);
    fx.listening();
    store.setMode("listening");
    store.setTranscript("Listening...");
    store.setResponse("Microphone is open.");

    try {
      const result = await listenCommand(store.languageMode);
      fx.response();
      store.setTranscript(result.transcript);
      store.setResponse(result.response);
      store.addVoiceHistory({ transcript: result.transcript, response: result.response });
      store.addConversation({ transcript: result.transcript, response: result.response });
      store.setMode("online");
    } catch (error) {
      store.setMode("error");
      store.setResponse(error.message || "Voice command failed.");
    } finally {
      if (restoreWake) {
        window.setTimeout(() => store.setWakeEnabled(true), 900);
      }
    }
  }

  async function runGlobalPushToTalkFlow() {
    fx.listening();
    store.setMode("listening");
    store.setTranscript("Push-to-talk activated.");
    store.setResponse("Listening from global voice runtime...");
    const result = await triggerGlobalPushToTalk();
    if (result) return result;
    return runVoiceFlow();
  }

  async function updateVoiceRuntimeFlow(patch) {
    const electronResult = await setElectronVoiceRuntime(patch);
    if (electronResult) {
      store.setVoiceRuntime(electronResult);
      return electronResult;
    }
    const result = await updateVoiceRuntime(patch);
    store.setVoiceRuntime(result.runtime || {});
    return result.runtime || {};
  }

  async function runTextFlow(text, options = {}) {
    const rawText = text.trim();
    const normalizedText = options.google || googlePrefixPattern.test(rawText) ? googleSearchCommand(rawText) : rawText;
    const now = Date.now();
    if (
      textCommandInFlight.current
      || (lastTextCommand.current.text === normalizedText && now - lastTextCommand.current.startedAt < 2500)
    ) {
      return { response: "That command is already running." };
    }
    textCommandInFlight.current = true;
    lastTextCommand.current = { text: normalizedText, startedAt: now };
    fx.click();
    store.setMode(options.agent ? "executing" : "thinking");
    store.setTranscript(normalizedText);
    const pendingResponse = options.agent ? "Planning and executing..." : "Thinking...";
    store.setResponse(options.agent ? "Planning and executing..." : "Working on it...");
    const conversationContext = store.chatHistory
      .slice(0, 12)
      .reverse()
      .map((item) => ({
        transcript: item.transcript,
        response: item.response,
      }));
    const conversationId = store.addConversation({ transcript: normalizedText, response: pendingResponse });
    store.addExecutionLog({ message: `Received command: ${normalizedText}`, level: "info" });

    try {
      const useStreaming = !options.agent && Boolean(store.aiProviderConfig?.settings?.streaming);
      let streamedResponse = "";
      const result = options.agent
        ? await executeAgentTask(normalizedText)
        : useStreaming
          ? await streamChatCommand(normalizedText, languageModeRef.current, conversationContext, (event) => {
              if (event.type !== "chunk") return;
              streamedResponse += event.text;
              store.setResponse(streamedResponse);
              if (conversationId) store.updateConversation(conversationId, { response: streamedResponse });
            })
          : await chatCommand(normalizedText, false, languageModeRef.current, conversationContext);
      fx.response();
      const response = result.response || result.summary || "Done.";
      store.setResponse(response);
      if (conversationId) {
        store.updateConversation(conversationId, { response });
      } else {
        store.addConversation({ transcript: text, response });
      }
      if (result.logs) store.setExecutionLogs(result.logs);
      store.setMode("online");
      return result;
    } catch (error) {
      store.setMode("error");
      const message = error.message || "Command failed.";
      store.setResponse(message);
      if (conversationId) {
        store.updateConversation(conversationId, { response: message });
      }
      store.addExecutionLog({ message, level: "error" });
      throw error;
    } finally {
      textCommandInFlight.current = false;
    }
  }

  async function previewPlanFlow(text) {
    fx.click();
    store.setMode("thinking");
    store.setTranscript(text);
    store.setResponse("Planning workflow...");
    const result = await previewAgentPlan(text);
    store.setResponse(result.response || "Plan ready.");
    const thinking = await getThinkingTimeline();
    store.setThinkingTimeline(thinking.thinking || [], thinking.control || undefined);
    store.setMode("online");
    return result;
  }

  async function pauseAgentFlow() {
    try {
      const result = await pauseAgentTask();
      store.addExecutionLog({ message: result.message || "Execution paused.", level: "warning" });
      const thinking = await getThinkingTimeline();
      store.setThinkingTimeline(thinking.thinking || [], thinking.control || undefined);
      return result;
    } catch (error) {
      store.addExecutionLog({ message: error.message || "Pause failed.", level: "error" });
      throw error;
    }
  }

  async function resumeAgentFlow() {
    try {
      const result = await resumeAgentTask();
      store.addExecutionLog({ message: result.message || "Execution resumed.", level: "info" });
      const thinking = await getThinkingTimeline();
      store.setThinkingTimeline(thinking.thinking || [], thinking.control || undefined);
      return result;
    } catch (error) {
      store.addExecutionLog({ message: error.message || "Resume failed.", level: "error" });
      throw error;
    }
  }

  async function cancelAgentFlow() {
    try {
      const result = await cancelAgentTask();
      store.addExecutionLog({ message: result.message || "Execution cancelled.", level: "warning" });
      const thinking = await getThinkingTimeline();
      store.setThinkingTimeline(thinking.thinking || [], thinking.control || undefined);
      return result;
    } catch (error) {
      store.addExecutionLog({ message: error.message || "Cancel failed.", level: "error" });
      throw error;
    }
  }

  async function captureVisionFlow() {
    fx.click();
    store.setMode("thinking");
    store.setResponse("Capturing and analyzing the current screen...");
    try {
      const result = await captureVisionScreenshot();
      store.setVision(result);
      store.setResponse(result.summary || "Screenshot analyzed.");
      store.addExecutionLog({ message: result.summary || "Screenshot analyzed.", level: result.ok ? "success" : "error" });
      store.setMode("online");
      return result;
    } catch (error) {
      store.setMode("error");
      store.setResponse(error.message || "Screenshot analysis failed.");
      throw error;
    }
  }

  async function startWorkflowRecordingFlow(name) {
    const result = await startWorkflowRecording(name);
    store.setWorkflowRecorder(result.recorder || {});
    store.addExecutionLog({ message: "Workflow recording started.", level: "running" });
    return result;
  }

  async function stopWorkflowRecordingFlow() {
    const result = await stopWorkflowRecording();
    store.setWorkflowRecorder(result.recorder || {});
    store.addExecutionLog({ message: "Workflow recording stopped.", level: "success" });
    return result;
  }

  async function replayWorkflowFlow(id) {
    fx.click();
    store.setMode("executing");
    const result = await replayWorkflow(id);
    store.setResponse(result.response || "Workflow replay complete.");
    if (result.logs) store.setExecutionLogs(result.logs);
    store.setMode("online");
    return result;
  }

  async function runAction(task) {
    fx.click();
    store.setMode("executing");
    store.setTranscript(`Action: ${task.replaceAll("_", " ")}`);
    store.setResponse("Executing...");
    store.addExecutionLog({ message: `Running system task: ${task}`, level: "running" });

    try {
      const result = await runSystemTask(task);
      fx.response();
      store.setResponse(result.response);
      store.addConversation({ transcript: `Action: ${task}`, response: result.response });
      store.addExecutionLog({ message: result.response, level: "success" });
      store.setMode("online");
    } catch (error) {
      store.setMode("error");
      store.setResponse(error.message || "System action failed.");
      store.addExecutionLog({ message: error.message || "System action failed.", level: "error" });
    }
  }

  async function handleUpload(file) {
    fx.click();
    store.setMode("indexing");
    store.setTranscript(`Upload: ${file.name}`);
    store.setResponse("Reading the file...");

    try {
      const result = await uploadFile(file);
      fx.response();
      store.addUpload(result);
      store.setResponse(result.summary);
      store.addConversation({ transcript: `Uploaded ${result.filename}`, response: result.summary });
      store.addExecutionLog({ message: `Indexed file: ${result.filename}`, level: "success" });
      store.setMode("online");
    } catch (error) {
      store.setMode("error");
      store.setResponse(error.message || "File upload failed.");
      store.addExecutionLog({ message: error.message || "File upload failed.", level: "error" });
    }
  }

  async function runBrowserFlow(text) {
    fx.click();
    store.setMode("executing");
    store.setTranscript(text);
    store.setResponse("Starting visual browser automation...");
    store.addExecutionLog({ message: `Browser task: ${text}`, level: "running" });

    try {
      const result = await runBrowserTask(text);
      store.setBrowserState(result);
      store.setResponse(result.response || "Browser task started.");
      store.addConversation({ transcript: text, response: result.response || "Browser task started." });
      store.setMode("online");
      return result;
    } catch (error) {
      store.setMode("error");
      store.setResponse(error.message || "Browser automation failed.");
      store.addExecutionLog({ message: error.message || "Browser automation failed.", level: "error" });
      throw error;
    }
  }

  async function pauseBrowserFlow() {
    try {
      const result = await pauseBrowserTask();
      store.setBrowserState(result);
      return result;
    } catch (error) {
      store.addExecutionLog({ message: error.message || "Browser pause failed.", level: "error" });
      throw error;
    }
  }

  async function resumeBrowserFlow() {
    try {
      const result = await resumeBrowserTask();
      store.setBrowserState(result);
      return result;
    } catch (error) {
      store.addExecutionLog({ message: error.message || "Browser resume failed.", level: "error" });
      throw error;
    }
  }

  async function stopBrowserFlow() {
    try {
      const result = await stopBrowserTask();
      store.setBrowserState(result);
      return result;
    } catch (error) {
      store.addExecutionLog({ message: error.message || "Browser stop failed.", level: "error" });
      throw error;
    }
  }

  async function closeBrowserFlow() {
    try {
      const result = await closeBrowserTask();
      store.setBrowserState(result);
      return result;
    } catch (error) {
      store.addExecutionLog({ message: error.message || "Browser close failed.", level: "error" });
      throw error;
    }
  }

  return {
    ...store,
    busy,
    activeWave,
    runVoiceFlow,
    runGlobalPushToTalkFlow,
    updateVoiceRuntimeFlow,
    runTextFlow,
    runBrowserFlow,
    previewPlanFlow,
    pauseAgentFlow,
    resumeAgentFlow,
    cancelAgentFlow,
    captureVisionFlow,
    startWorkflowRecordingFlow,
    stopWorkflowRecordingFlow,
    replayWorkflowFlow,
    pauseBrowserFlow,
    resumeBrowserFlow,
    stopBrowserFlow,
    closeBrowserFlow,
    runAction,
    handleUpload,
  };
}
