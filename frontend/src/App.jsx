import { useEffect, useMemo, useRef, useState } from "react";

import CompactFeed from "./components/CompactFeed.jsx";
import CompactStatus from "./components/CompactStatus.jsx";
import CommandConsole from "./components/CommandConsole.jsx";
import CoreStage from "./components/CoreStage.jsx";
import QuickDock from "./components/QuickDock.jsx";
import WindowTitleBar from "./components/WindowTitleBar.jsx";
import { chatCommand, greetCommand, health, listenCommand, runSystemTask, uploadFile, wakeListen } from "./lib/api.js";
import { fx } from "./lib/sounds.js";

const startupMessage = "Good day. JX JARVIS systems are online and ready.";
const wait = (milliseconds) => new Promise((resolve) => window.setTimeout(resolve, milliseconds));

export default function App() {
  const [now, setNow] = useState(new Date());
  const [mode, setMode] = useState("online");
  const [backendOnline, setBackendOnline] = useState(false);
  const [wakeEnabled, setWakeEnabled] = useState(true);
  const [transcript, setTranscript] = useState("Awaiting voice command.");
  const [response, setResponse] = useState(startupMessage);
  const [history, setHistory] = useState([]);
  const [uploads, setUploads] = useState([]);
  const fileInputRef = useRef(null);
  const greetingStarted = useRef(false);
  const modeRef = useRef(mode);
  const wakeLoopActive = useRef(false);
  const busy = ["listening", "thinking", "speaking", "executing", "indexing"].includes(mode);

  useEffect(() => {
    const timer = window.setInterval(() => setNow(new Date()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    modeRef.current = mode;
  }, [mode]);

  useEffect(() => {
    fx.startup();
    const check = async () => {
      try {
        await health();
        setBackendOnline(true);
        if (!greetingStarted.current && !window.sessionStorage.getItem("jxJarvisGreeted")) {
          greetingStarted.current = true;
          window.sessionStorage.setItem("jxJarvisGreeted", "true");
          setMode("speaking");
          setTranscript("Startup greeting");
          setResponse("Initializing personal greeting...");
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
          const result = await wakeListen(2.8);
          if (cancelled) break;

          if (!result.awakened) {
            setMode("online");
            await wait(450);
            continue;
          }

          fx.response();
          const heard = result.command ? `Hey Jarvis: ${result.command}` : result.transcript;
          setTranscript(heard);
          setResponse(result.response || "Wake phrase detected.");

          if (result.response) {
            setHistory((items) => [{ transcript: heard, response: result.response }, ...items].slice(0, 5));
          }

          if (result.status === "awake") {
            setMode("listening");
            setResponse("Wake phrase confirmed. Listening for your command...");
            const followUp = await listenCommand();
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
  }, [backendOnline, wakeEnabled]);

  const activeWave = useMemo(() => busy || mode === "online" || mode === "wake", [busy, mode]);

  async function runVoiceFlow() {
    const restoreWake = wakeEnabled;
    setWakeEnabled(false);
    fx.listening();
    setMode("listening");
    setTranscript("Listening...");
    setResponse("Microphone channel open.");

    try {
      const result = await listenCommand();
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
    setResponse("Processing command...");

    try {
      const result = await chatCommand(text, true);
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
    setTranscript(`System task: ${task.replaceAll("_", " ")}`);
    setResponse("Executing safe local action...");

    try {
      const result = await runSystemTask(task);
      fx.response();
      setResponse(result.response);
      setHistory((items) => [{ transcript: `System task: ${task}`, response: result.response }, ...items].slice(0, 5));
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
    setResponse("Receiving file into the local intake bay...");

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
    <main className="relative min-h-screen overflow-hidden bg-void text-white">
      <div className="hud-grid absolute inset-0" />
      <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(180deg,transparent,rgba(56,246,255,.04),transparent)] animate-scan" />

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

        <div className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-4 px-4 py-4 sm:px-6">
          <header className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h1 className="font-display text-3xl font-bold uppercase tracking-[0.28em] text-white drop-shadow-[0_0_18px_rgba(56,246,255,.35)]">
                JX JARVIS
              </h1>
              <p className="mt-1 text-xs uppercase tracking-[0.3em] text-cyanSoft/65">Compact Voice Console</p>
            </div>
            <CompactStatus mode={mode} backendOnline={backendOnline} wakeEnabled={wakeEnabled} now={now} />
          </header>

          <div className="grid flex-1 grid-cols-1 gap-4 lg:grid-cols-[minmax(360px,1fr)_420px]">
            <CoreStage mode={mode} activeWave={activeWave} backendOnline={backendOnline} busy={busy} onVoice={runVoiceFlow} />
            <div className="flex flex-col gap-4">
              <CompactFeed transcript={transcript} response={response} history={history} />
              {uploads.length > 0 && (
                <div className="rounded-2xl border border-cyanCore/15 bg-black/25 p-3">
                  <p className="mb-2 text-[11px] uppercase tracking-[0.22em] text-cyanSoft/55">Last Upload</p>
                  <p className="truncate text-sm text-white/75">{uploads[0].filename}</p>
                </div>
              )}
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
          <CommandConsole onSend={runTextFlow} disabled={!backendOnline || busy} />
        </div>
      </div>
    </main>
  );
}
