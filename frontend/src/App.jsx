import { useEffect, useMemo, useRef, useState } from "react";
import { motion } from "framer-motion";
import {
  Bell,
  Bot,
  Brain,
  CheckCircle2,
  Files,
  FolderOpen,
  Home,
  MessageCircle,
  Mic2,
  MonitorUp,
  Settings,
  Sparkles,
  Workflow,
} from "lucide-react";

import CompactFeed from "./components/CompactFeed.jsx";
import CompactStatus from "./components/CompactStatus.jsx";
import CommandConsole from "./components/CommandConsole.jsx";
import CoreStage from "./components/CoreStage.jsx";
import LanguageMode from "./components/LanguageMode.jsx";
import QuickDock from "./components/QuickDock.jsx";
import WindowTitleBar from "./components/WindowTitleBar.jsx";
import { chatCommand, greetCommand, health, listenCommand, runSystemTask, uploadFile, wakeListen } from "./lib/api.js";
import { fx } from "./lib/sounds.js";

const startupMessage = "Jarvis is ready. Ask for an action or start a conversation.";
const wait = (milliseconds) => new Promise((resolve) => window.setTimeout(resolve, milliseconds));

const navigation = [
  { label: "Home", icon: Home, active: true },
  { label: "Chat", icon: MessageCircle },
  { label: "Voice", icon: Mic2 },
  { label: "Files", icon: Files },
  { label: "Automation", icon: Workflow },
  { label: "Browser", icon: MonitorUp },
  { label: "Settings", icon: Settings },
];

export default function App() {
  const [now, setNow] = useState(new Date());
  const [mode, setMode] = useState("online");
  const [backendOnline, setBackendOnline] = useState(false);
  const [userName, setUserName] = useState("User");
  const [wakeEnabled, setWakeEnabled] = useState(true);
  const [languageMode, setLanguageMode] = useState(() => window.localStorage.getItem("jxJarvisLanguageMode") || "auto");
  const [transcript, setTranscript] = useState("Awaiting command.");
  const [response, setResponse] = useState(startupMessage);
  const [history, setHistory] = useState([]);
  const [uploads, setUploads] = useState([]);
  const fileInputRef = useRef(null);
  const greetingStarted = useRef(false);
  const modeRef = useRef(mode);
  const wakeLoopActive = useRef(false);
  const busy = ["listening", "thinking", "speaking", "executing", "indexing", "coding", "memory"].includes(mode);

  useEffect(() => {
    const timer = window.setInterval(() => setNow(new Date()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    modeRef.current = mode;
  }, [mode]);

  useEffect(() => {
    window.localStorage.setItem("jxJarvisLanguageMode", languageMode);
  }, [languageMode]);

  useEffect(() => {
    fx.startup();
    const check = async () => {
      try {
        const result = await health();
        setUserName(result.profile?.user_name || "User");
        setBackendOnline(true);
        if (!greetingStarted.current && !window.sessionStorage.getItem("jxJarvisGreeted")) {
          greetingStarted.current = true;
          window.sessionStorage.setItem("jxJarvisGreeted", "true");
          setMode("speaking");
          setTranscript("Startup greeting");
          setResponse("Preparing workspace...");
          const result = await greetCommand();
          setTranscript(result.transcript);
          setResponse(result.response);
          setHistory((items) => [{ transcript: result.transcript, response: result.response }, ...items].slice(0, 5));
          setMode("online");
        }
      } catch {
        setBackendOnline(false);
      }
    };
    check();
    const poll = window.setInterval(check, 3500);
    return () => window.clearInterval(poll);
  }, []);

  useEffect(() => {
    if (!wakeEnabled || !backendOnline) return undefined;

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
          setMode("wake");
          const result = await wakeListen(2.8, languageMode);
          if (cancelled) break;

          if (!result.awakened) {
            setMode("online");
            await wait(450);
            continue;
          }

          fx.response();
          const heard = result.command ? `Hey Jarvis: ${result.command}` : result.transcript;
          setTranscript(heard);
          setResponse(result.response || "Listening.");

          if (result.response) {
            setHistory((items) => [{ transcript: heard, response: result.response }, ...items].slice(0, 5));
          }

          if (result.status === "awake") {
            setMode("listening");
            setResponse("Listening for your command...");
            const followUp = await listenCommand(languageMode);
            if (cancelled) break;
            fx.response();
            setTranscript(followUp.transcript);
            setResponse(followUp.response);
            setHistory((items) => [{ transcript: followUp.transcript, response: followUp.response }, ...items].slice(0, 5));
          }

          setMode("online");
          await wait(1200);
        } catch {
          if (!cancelled) {
            setMode("online");
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
  }, [backendOnline, wakeEnabled, languageMode]);

  const activeWave = useMemo(() => busy || mode === "online" || mode === "wake", [busy, mode]);

  async function runVoiceFlow() {
    const restoreWake = wakeEnabled;
    setWakeEnabled(false);
    fx.listening();
    setMode("listening");
    setTranscript("Listening...");
    setResponse("Microphone is open.");

    try {
      const result = await listenCommand(languageMode);
      fx.response();
      setTranscript(result.transcript);
      setResponse(result.response);
      setHistory((items) => [{ transcript: result.transcript, response: result.response }, ...items].slice(0, 5));
      setMode("online");
    } catch (error) {
      setMode("error");
      setResponse(error.message || "Voice command failed.");
    } finally {
      if (restoreWake) {
        window.setTimeout(() => setWakeEnabled(true), 900);
      }
    }
  }

  async function runTextFlow(text) {
    fx.click();
    setMode("thinking");
    setTranscript(text);
    setResponse("Working on it...");

    try {
      const result = await chatCommand(text, true, languageMode);
      fx.response();
      setResponse(result.response);
      setHistory((items) => [{ transcript: text, response: result.response }, ...items].slice(0, 5));
      setMode("online");
    } catch (error) {
      setMode("error");
      setResponse(error.message || "Command failed.");
    }
  }

  async function runAction(task) {
    fx.click();
    setMode("executing");
    setTranscript(`Action: ${task.replaceAll("_", " ")}`);
    setResponse("Executing...");

    try {
      const result = await runSystemTask(task);
      fx.response();
      setResponse(result.response);
      setHistory((items) => [{ transcript: `Action: ${task}`, response: result.response }, ...items].slice(0, 5));
      setMode("online");
    } catch (error) {
      setMode("error");
      setResponse(error.message || "System action failed.");
    }
  }

  async function handleUpload(file) {
    fx.click();
    setMode("indexing");
    setTranscript(`Upload: ${file.name}`);
    setResponse("Reading the file...");

    try {
      const result = await uploadFile(file);
      fx.response();
      setUploads((items) => [result, ...items].slice(0, 4));
      setResponse(result.summary);
      setHistory((items) => [{ transcript: `Uploaded ${result.filename}`, response: result.summary }, ...items].slice(0, 5));
      setMode("online");
    } catch (error) {
      setMode("error");
      setResponse(error.message || "File upload failed.");
    }
  }

  return (
    <main className="relative min-h-screen overflow-hidden bg-void text-textPrimary">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,rgba(0,229,255,.08),transparent_30%)]" />

      <div className="relative z-10 flex min-h-screen flex-col">
        <WindowTitleBar />

        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept="text/*,image/*,audio/*,video/*,.pdf,.json,.csv,.md,.py,.js,.jsx,.ts,.tsx"
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) handleUpload(file);
            event.target.value = "";
          }}
        />

        <div className="mx-auto flex w-full max-w-[1600px] flex-1 gap-4 p-4">
          <Sidebar userName={userName} />

          <div className="flex min-w-0 flex-1 flex-col gap-4">
            <TopBar
              mode={mode}
              backendOnline={backendOnline}
              wakeEnabled={wakeEnabled}
              now={now}
              languageMode={languageMode}
              busy={busy}
              onLanguageChange={setLanguageMode}
            />

            <div className="grid min-h-0 flex-1 grid-cols-1 gap-4 xl:grid-cols-[minmax(0,1fr)_360px]">
              <div className="flex min-w-0 flex-col gap-4">
                <CoreStage
                  mode={mode}
                  activeWave={activeWave}
                  backendOnline={backendOnline}
                  busy={busy}
                  onVoice={runVoiceFlow}
                  onSuggestion={runTextFlow}
                />

                <section className="panel rounded-[28px] p-5">
                  <div className="mb-4 flex items-center justify-between">
                    <div>
                      <h2 className="text-base font-semibold text-textPrimary">Quick commands</h2>
                      <p className="mt-1 text-sm text-textSecondary">Run frequent actions without leaving the workspace.</p>
                    </div>
                  </div>
                  <QuickDock
                    disabled={!backendOnline || busy}
                    wakeEnabled={wakeEnabled}
                    onRun={runAction}
                    onToggleWake={() => {
                      fx.click();
                      setWakeEnabled((enabled) => !enabled);
                      setMode("online");
                    }}
                    onUploadClick={() => fileInputRef.current?.click()}
                  />
                </section>
              </div>

              <aside className="flex min-w-0 flex-col gap-4">
                <CompactFeed transcript={transcript} response={response} history={history} />
                <UtilityPanel mode={mode} backendOnline={backendOnline} wakeEnabled={wakeEnabled} uploads={uploads} history={history} />
              </aside>
            </div>

            <CommandConsole onSend={runTextFlow} disabled={!backendOnline || busy} />
          </div>
        </div>
      </div>
    </main>
  );
}

function Sidebar({ userName }) {
  return (
    <aside className="app-surface hidden w-64 shrink-0 flex-col rounded-[28px] p-4 lg:flex">
      <div className="flex items-center gap-3 px-2 py-2">
        <div className="grid h-10 w-10 place-items-center rounded-2xl bg-cyanCore text-sm font-bold text-[#041018]">JX</div>
        <div>
          <p className="font-semibold text-textPrimary">JX Jarvis</p>
          <p className="text-sm text-textSecondary">AI Workspace</p>
        </div>
      </div>

      <nav className="mt-6 space-y-1">
        {navigation.map(({ label, icon: Icon, active }) => (
          <button
            key={label}
            type="button"
            className={`flex h-11 w-full items-center gap-3 rounded-2xl px-3 text-sm font-medium transition ${
              active ? "bg-white/[0.075] text-textPrimary" : "text-textSecondary hover:bg-white/[0.045] hover:text-textPrimary"
            }`}
          >
            <Icon size={17} />
            {label}
          </button>
        ))}
      </nav>

      <div className="mt-auto rounded-3xl border border-line bg-white/[0.035] p-4">
        <div className="mb-3 flex items-center gap-2 text-sm font-medium text-textPrimary">
          <Sparkles size={16} className="text-cyanCore" />
          Workspace profile
        </div>
        <p className="text-sm text-textSecondary">Signed in locally as</p>
        <p className="mt-1 truncate font-medium text-textPrimary">{userName}</p>
      </div>
    </aside>
  );
}

function TopBar({ mode, backendOnline, wakeEnabled, now, languageMode, busy, onLanguageChange }) {
  return (
    <header className="app-surface flex flex-wrap items-center justify-between gap-3 rounded-[28px] px-5 py-4">
      <div>
        <p className="text-sm text-textSecondary">Personal AI Workspace</p>
        <h1 className="mt-1 text-2xl font-semibold tracking-[-0.03em] text-textPrimary">Command Center</h1>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <LanguageMode value={languageMode} disabled={busy} onChange={onLanguageChange} />
        <CompactStatus mode={mode} backendOnline={backendOnline} wakeEnabled={wakeEnabled} now={now} />
      </div>
    </header>
  );
}

function UtilityPanel({ mode, backendOnline, wakeEnabled, uploads, history }) {
  const activity = history.slice(0, 4);

  return (
    <section className="panel rounded-[28px] p-5">
      <div className="mb-5 flex items-center justify-between">
        <h2 className="text-base font-semibold text-textPrimary">Utilities</h2>
        <Bell size={17} className="text-textSecondary" />
      </div>

      <div className="space-y-3">
        <Widget icon={CheckCircle2} title="System status" value={backendOnline ? "Online and ready" : "Backend offline"} accent={backendOnline ? "emerald" : "red"} />
        <Widget icon={Mic2} title="Voice engine" value={wakeEnabled ? "Wake listening enabled" : "Push-to-talk only"} accent={wakeEnabled ? "cyan" : "slate"} />
        <Widget icon={Brain} title="Memory" value="Local profile available" accent="slate" />
        <Widget icon={FolderOpen} title="Latest upload" value={uploads[0]?.filename || "No recent uploads"} accent="slate" />
      </div>

      <div className="mt-6">
        <p className="mb-3 text-sm font-medium text-textPrimary">Running tasks</p>
        <div className="rounded-2xl border border-line bg-white/[0.025] p-3">
          <div className="flex items-center gap-2">
            <span className={`h-2 w-2 rounded-full ${mode === "online" ? "bg-emerald-400" : "bg-cyanCore animate-softPulse"}`} />
            <p className="text-sm text-textPrimary">{mode === "online" ? "Idle" : mode.charAt(0).toUpperCase() + mode.slice(1)}</p>
          </div>
          <p className="mt-1 text-sm text-textSecondary">Jarvis responds with short action confirmations.</p>
        </div>
      </div>

      <div className="mt-6">
        <p className="mb-3 text-sm font-medium text-textPrimary">Recent activity</p>
        <div className="space-y-2">
          {activity.length ? (
            activity.map((item, index) => (
              <div key={`${item.transcript}-${index}`} className="rounded-2xl border border-line bg-white/[0.025] p-3">
                <p className="truncate text-sm text-textPrimary">{item.transcript}</p>
                <p className="mt-1 truncate text-xs text-textSecondary">{item.response}</p>
              </div>
            ))
          ) : (
            <p className="rounded-2xl border border-line bg-white/[0.025] p-3 text-sm text-textSecondary">No recent activity yet.</p>
          )}
        </div>
      </div>
    </section>
  );
}

function Widget({ icon: Icon, title, value, accent }) {
  const color =
    accent === "emerald" ? "text-emerald-400 bg-emerald-400/10" : accent === "red" ? "text-red-400 bg-red-400/10" : "text-cyanCore bg-cyanCore/10";

  return (
    <div className="rounded-2xl border border-line bg-white/[0.025] p-3">
      <div className="flex items-start gap-3">
        <div className={`grid h-9 w-9 shrink-0 place-items-center rounded-2xl ${color}`}>
          <Icon size={17} />
        </div>
        <div className="min-w-0">
          <p className="text-sm font-medium text-textPrimary">{title}</p>
          <p className="mt-1 truncate text-sm text-textSecondary">{value}</p>
        </div>
      </div>
    </div>
  );
}
