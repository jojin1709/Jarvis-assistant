import { NavLink, Outlet } from "react-router-dom";
import { Bell, Bot, Files, Home, MessageCircle, Mic2, MonitorUp, Settings, Sparkles, Workflow } from "lucide-react";
import { useEffect, useState } from "react";

import CommandConsole from "../components/CommandConsole.jsx";
import CommandPalette from "../components/CommandPalette.jsx";
import CompactStatus from "../components/CompactStatus.jsx";
import LanguageMode from "../components/LanguageMode.jsx";
import LogoMark from "../components/LogoMark.jsx";
import WindowTitleBar from "../components/WindowTitleBar.jsx";
import { useJarvisRuntime } from "../hooks/useJarvisRuntime.js";
import AssistantOverlay from "../overlays/AssistantOverlay.jsx";

const navigation = [
  { label: "Home", path: "/", icon: Home },
  { label: "Chat", path: "/chat", icon: MessageCircle },
  { label: "Voice", path: "/voice", icon: Mic2 },
  { label: "Files", path: "/files", icon: Files },
  { label: "Automation", path: "/automation", icon: Workflow },
  { label: "Browser", path: "/browser", icon: MonitorUp },
  { label: "Settings", path: "/settings", icon: Settings },
];

export default function AppShell() {
  const runtime = useJarvisRuntime();
  const [now, setNow] = useState(new Date());
  const [overlayOpen, setOverlayOpen] = useState(false);

  useEffect(() => {
    const timer = window.setInterval(() => setNow(new Date()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    function onKeyDown(event) {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        runtime.setCommandPaletteOpen(true);
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [runtime.setCommandPaletteOpen]);

  useEffect(() => {
    if (!window.jxJarvis?.onGlobalCommand) return undefined;
    return window.jxJarvis.onGlobalCommand((command) => {
      if (command === "command-palette") {
        runtime.setCommandPaletteOpen(true);
      }
      if (command === "assistant-overlay") {
        setOverlayOpen(true);
      }
    });
  }, [runtime.setCommandPaletteOpen]);

  return (
    <main className="relative min-h-screen overflow-hidden bg-void text-textPrimary">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,rgba(0,229,255,.08),transparent_30%)]" />
      <div className="relative z-10 flex min-h-screen flex-col">
        <WindowTitleBar />

        <div className="mx-auto flex w-full max-w-[1600px] flex-1 gap-4 p-4">
          <Sidebar userName={runtime.userName} />

          <div className="flex min-w-0 flex-1 flex-col gap-4">
            <header className="app-surface flex flex-wrap items-center justify-between gap-3 rounded-[28px] px-5 py-4">
              <div>
                <p className="text-sm text-textSecondary">Personal AI Workspace</p>
                <h1 className="mt-1 text-2xl font-semibold tracking-[-0.03em] text-textPrimary">Command Center</h1>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <button
                  type="button"
                  onClick={() => runtime.setCommandPaletteOpen(true)}
                  className="rounded-2xl border border-line bg-white/[0.035] px-3 py-2 text-sm text-textSecondary transition hover:bg-white/[0.055] hover:text-textPrimary"
                >
                  Ctrl K
                </button>
                <LanguageMode value={runtime.languageMode} disabled={runtime.busy} onChange={runtime.setLanguageMode} />
                <CompactStatus mode={runtime.mode} backendOnline={runtime.backendOnline} wakeEnabled={runtime.wakeEnabled} now={now} />
              </div>
            </header>

            <div className="min-h-0 flex-1">
              <Outlet context={runtime} />
            </div>

            <CommandConsole onSend={runtime.runTextFlow} disabled={!runtime.backendOnline || runtime.busy} />
          </div>
        </div>
      </div>

      <CommandPalette
        open={runtime.commandPaletteOpen}
        onClose={() => runtime.setCommandPaletteOpen(false)}
        onRun={runtime.runTextFlow}
      />
      <AssistantOverlay open={overlayOpen} onClose={() => setOverlayOpen(false)} runtime={runtime} />
    </main>
  );
}

function Sidebar({ userName }) {
  return (
    <aside className="app-surface hidden w-64 shrink-0 flex-col rounded-[28px] p-4 lg:flex">
      <div className="flex items-center gap-3 px-2 py-2">
        <LogoMark className="h-10 w-10" rounded="rounded-2xl" />
        <div>
          <p className="font-semibold text-textPrimary">JX Jarvis</p>
          <p className="text-sm text-textSecondary">AI Workspace</p>
        </div>
      </div>

      <nav className="mt-6 space-y-1">
        {navigation.map(({ label, path, icon: Icon }) => (
          <NavLink
            key={path}
            to={path}
            end={path === "/"}
            className={({ isActive }) =>
              `flex h-11 w-full items-center gap-3 rounded-2xl px-3 text-sm font-medium transition ${
                isActive ? "bg-white/[0.075] text-textPrimary" : "text-textSecondary hover:bg-white/[0.045] hover:text-textPrimary"
              }`
            }
          >
            <Icon size={17} />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="mt-auto space-y-3">
        <div className="rounded-3xl border border-line bg-white/[0.035] p-4">
          <div className="mb-3 flex items-center gap-2 text-sm font-medium text-textPrimary">
            <Sparkles size={16} className="text-cyanCore" />
            Workspace profile
          </div>
          <p className="text-sm text-textSecondary">Signed in locally as</p>
          <p className="mt-1 truncate font-medium text-textPrimary">{userName}</p>
        </div>
        <div className="rounded-3xl border border-line bg-white/[0.035] p-4">
          <div className="flex items-center gap-2 text-sm text-textSecondary">
            <Bell size={16} />
            Notifications stay local
          </div>
        </div>
        <div className="rounded-3xl border border-line bg-white/[0.035] p-4">
          <p className="text-xs uppercase tracking-[0.18em] text-textSecondary">Created by</p>
          <a
            href="https://www.linkedin.com/in/jojin-john-74386b34a"
            target="_blank"
            rel="noreferrer"
            className="mt-1 block truncate text-sm font-medium text-textPrimary transition hover:text-cyanCore"
          >
            Jojin John
          </a>
        </div>
      </div>
    </aside>
  );
}
