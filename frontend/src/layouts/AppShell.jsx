import { NavLink, Outlet, useLocation } from "react-router-dom";
import { AppWindow, Bell, Bot, Files, Home, MessageCircle, Mic2, MonitorUp, Settings, Sparkles, Workflow } from "lucide-react";
import { Component, useEffect, useRef, useState } from "react";

import CommandConsole from "../components/CommandConsole.jsx";
import CommandPalette from "../components/CommandPalette.jsx";
import CompactStatus from "../components/CompactStatus.jsx";
import LanguageMode from "../components/LanguageMode.jsx";
import LogoMark from "../components/LogoMark.jsx";
import WindowTitleBar from "../components/WindowTitleBar.jsx";
import { useKeyboardShortcuts } from "../hooks/useKeyboardShortcuts.js";
import { useJarvisRuntime } from "../hooks/useJarvisRuntime.js";
import { useTheme } from "../hooks/useTheme.js";
import AssistantOverlay from "../overlays/AssistantOverlay.jsx";

const navigation = [
  { label: "Home", path: "/", icon: Home },
  { label: "Chat", path: "/chat", icon: MessageCircle },
  { label: "Voice", path: "/voice", icon: Mic2 },
  { label: "Files", path: "/files", icon: Files },
  { label: "Apps", path: "/apps", icon: AppWindow },
  { label: "Automation", path: "/automation", icon: Workflow },
  { label: "Browser", path: "/browser", icon: MonitorUp },
  { label: "Settings", path: "/settings", icon: Settings },
];

export default function AppShell() {
  const runtime = useJarvisRuntime();
  const location = useLocation();
  const contentRef = useRef(null);
  const [now, setNow] = useState(new Date());
  const [overlayOpen, setOverlayOpen] = useState(false);
  useTheme();

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

  useKeyboardShortcuts({
    onFocusChat: () => runtime.setCommandPaletteOpen(true),
    onNewChat: runtime.startNewChat,
    onToggleVoice: () => runtime.setWakeEnabled(!runtime.wakeEnabled),
  });

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

  useEffect(() => {
    contentRef.current?.scrollTo({ top: 0, left: 0 });
  }, [location.pathname]);

  return (
    <main className="relative h-screen overflow-hidden bg-void text-textPrimary">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,rgba(0,229,255,.08),transparent_30%)]" />
      <div className="relative z-10 flex h-full min-h-0 flex-col">
        <WindowTitleBar />

        <div className="flex min-h-0 w-full flex-1 gap-3 p-3">
          <Sidebar userName={runtime.userName} />

          <div className="flex min-h-0 min-w-0 flex-1 flex-col gap-3">
            <header className="app-surface shrink-0 flex flex-wrap items-center justify-between gap-3 rounded-[24px] px-5 py-3">
              <div>
                <p className="text-sm text-textSecondary">Personal AI Workspace</p>
                <h1 className="text-2xl font-semibold tracking-[-0.03em] text-textPrimary">Command Center</h1>
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

            <div ref={contentRef} className="min-h-0 flex-1 overflow-y-auto overflow-x-hidden pr-1">
              <ErrorBoundary>
                <Outlet context={runtime} />
              </ErrorBoundary>
            </div>

            <div className="shrink-0">
              <CommandConsole onSend={runtime.runTextFlow} disabled={!runtime.backendOnline || runtime.busy} />
            </div>
          </div>
        </div>
      </div>

      <CommandPalette
        open={runtime.commandPaletteOpen}
        onClose={() => runtime.setCommandPaletteOpen(false)}
        onRun={runtime.runTextFlow}
        disabled={!runtime.backendOnline || runtime.busy}
      />
      <AssistantOverlay open={overlayOpen} onClose={() => setOverlayOpen(false)} runtime={runtime} />
    </main>
  );
}

class ErrorBoundary extends Component {
  state = { error: null };

  static getDerivedStateFromError(error) {
    return { error };
  }

  render() {
    if (this.state.error) {
      return (
        <div className="flex h-full items-center justify-center p-8 text-center">
          <div>
            <p className="font-semibold text-textPrimary">Something went wrong</p>
            <p className="mt-2 text-sm text-textSecondary">{this.state.error.message}</p>
            <button className="mt-4 rounded-xl bg-cyanCore/10 px-4 py-2 text-sm text-cyanCore" onClick={() => this.setState({ error: null })}>
              Try again
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

function Sidebar({ userName }) {
  return (
    <aside className="app-surface hidden min-h-0 w-60 shrink-0 flex-col overflow-y-auto rounded-[24px] p-3 lg:flex">
      <div className="flex items-center gap-3 px-2 py-2">
        <LogoMark className="h-10 w-10" rounded="rounded-2xl" />
        <div>
          <p className="font-semibold text-textPrimary">JX Jarvis</p>
          <p className="text-sm text-textSecondary">AI Workspace</p>
        </div>
      </div>

      <nav className="mt-5 space-y-1">
        {navigation.map(({ label, path, icon: Icon }) => (
          <NavLink
            key={path}
            to={path}
            end={path === "/"}
            className={({ isActive }) =>
              `flex h-10 w-full items-center gap-3 rounded-2xl px-3 text-sm font-medium transition ${
                isActive ? "bg-white/[0.075] text-textPrimary" : "text-textSecondary hover:bg-white/[0.045] hover:text-textPrimary"
              }`
            }
          >
            <Icon size={17} />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="mt-auto space-y-2">
        <div className="rounded-2xl border border-line bg-white/[0.035] p-3">
          <div className="mb-3 flex items-center gap-2 text-sm font-medium text-textPrimary">
            <Sparkles size={16} className="text-cyanCore" />
            Workspace profile
          </div>
          <p className="text-sm text-textSecondary">Signed in locally as</p>
          <p className="mt-1 truncate font-medium text-textPrimary">{userName}</p>
        </div>
        <div className="rounded-2xl border border-line bg-white/[0.035] p-3">
          <div className="flex items-center gap-2 text-sm text-textSecondary">
            <Bell size={16} />
            Notifications stay local
          </div>
        </div>
        <div className="rounded-2xl border border-line bg-white/[0.035] p-3">
          <p className="text-xs uppercase tracking-[0.18em] text-textSecondary">Created by</p>
          <a
            href="https://www.linkedin.com/in/jojin-john-74386b34a"
            target="_blank"
            rel="noreferrer"
            onClick={(event) => {
              if (!window.jxJarvis?.openExternal) return;
              event.preventDefault();
              window.jxJarvis.openExternal("https://www.linkedin.com/in/jojin-john-74386b34a");
            }}
            className="mt-1 block truncate text-sm font-medium text-textPrimary transition hover:text-cyanCore"
          >
            Jojin John
          </a>
        </div>
      </div>
    </aside>
  );
}
