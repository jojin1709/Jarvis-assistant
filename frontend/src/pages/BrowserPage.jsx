import { useMemo, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { Bot, CircleStop, Globe2, MousePointerClick, Pause, Play, Power, RotateCcw, Search, SquareMousePointer, TextCursorInput } from "lucide-react";

import { API_BASE } from "../services/api.js";

const quickTasks = [
  "Search Google for best AI tools",
  "Open YouTube and search cybersecurity tutorials",
  "Open GitHub",
  "Open Stack Overflow",
  "Summarize page",
  "Scroll page",
];

export default function BrowserPage() {
  const runtime = useOutletContext();
  const browser = runtime.browserState || {};
  const [task, setTask] = useState("Search Google for best AI tools");
  const running = browser.status === "running";
  const paused = browser.status === "paused";
  const screenshot = browser.screenshotUrl ? `${API_BASE}${browser.screenshotUrl}` : null;

  const domItems = useMemo(() => {
    const summary = browser.domSummary || {};
    return [
      ["Inputs", summary.inputs || [], TextCursorInput],
      ["Buttons", summary.buttons || [], SquareMousePointer],
      ["Links", summary.links || [], Globe2],
    ];
  }, [browser.domSummary]);

  return (
    <div className="grid min-h-full gap-3 xl:grid-cols-[minmax(0,1fr)_360px]">
      <section className="panel flex min-h-0 flex-col overflow-hidden rounded-[24px]">
        <div className="shrink-0 border-b border-line p-4">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 className="text-xl font-semibold tracking-[-0.03em] text-textPrimary">Visual Browser Operator</h2>
              <p className="mt-1 text-sm text-textSecondary">Jarvis can open a visible browser, inspect the DOM, type, click, scroll, and verify page state.</p>
            </div>
            <span className={`rounded-full border px-3 py-1.5 text-xs font-semibold capitalize ${running ? "border-cyanCore/40 text-cyanCore" : paused ? "border-amber-300/30 text-amber-200" : "border-line text-textSecondary"}`}>
              {browser.status || "idle"}
            </span>
          </div>

          <form
            className="mt-3 flex items-center gap-2 rounded-[20px] border border-line bg-white/[0.035] p-2"
            onSubmit={(event) => {
              event.preventDefault();
              if (runtime.backendOnline && task.trim() && !running) runtime.runBrowserFlow(task.trim());
            }}
          >
            <Bot size={19} className="ml-2 text-cyanCore" />
            <input
              value={task}
              onChange={(event) => setTask(event.target.value)}
              className="min-w-0 flex-1 bg-transparent px-2 py-2 text-sm text-textPrimary outline-none placeholder:text-textSecondary"
              placeholder="Ask Jarvis to browse, search, click, scroll, or summarize..."
            />
            <button disabled={!runtime.backendOnline || !task.trim() || running} className="grid h-10 w-10 place-items-center rounded-2xl bg-cyanCore text-[#021018] disabled:opacity-45" type="submit">
              <Search size={18} />
            </button>
          </form>

          <div className="mt-3 flex flex-wrap gap-2">
            <ControlButton icon={Pause} label="Pause" disabled={!running} onClick={runtime.pauseBrowserFlow} />
            <ControlButton icon={Play} label="Resume" disabled={!paused} onClick={runtime.resumeBrowserFlow} />
            <ControlButton icon={CircleStop} label="Stop" disabled={!running && !paused} onClick={runtime.stopBrowserFlow} danger />
            <ControlButton icon={Power} label="Close browser" disabled={running} onClick={runtime.closeBrowserFlow} />
            <button
              type="button"
              onClick={() => runtime.runBrowserFlow(task.trim())}
              disabled={!runtime.backendOnline || running || !task.trim()}
              className="inline-flex h-10 items-center gap-2 rounded-2xl border border-line px-3 text-sm text-textSecondary transition hover:text-textPrimary disabled:opacity-40"
            >
              <RotateCcw size={15} />
              Run again
            </button>
          </div>
        </div>

        <div className="grid min-h-0 flex-1 gap-0 2xl:grid-cols-[minmax(0,1fr)_300px]">
          <div className="flex min-h-0 flex-col bg-[#02050b] p-3">
            <div className="mb-3 flex items-center justify-between gap-3 rounded-2xl border border-line bg-white/[0.03] px-3 py-2">
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-textPrimary">{browser.title || "No page loaded"}</p>
                <p className="truncate text-xs text-textSecondary">{browser.currentUrl || "Visible browser will appear here after the first task."}</p>
              </div>
              <MousePointerClick size={18} className="shrink-0 text-cyanCore" />
            </div>

            <div className="relative grid min-h-0 flex-1 place-items-center overflow-hidden rounded-[20px] border border-line bg-[#050914]">
              {screenshot ? (
                <img src={screenshot} alt="Live browser automation preview" className="h-full max-h-full w-full object-contain" />
              ) : (
                <div className="max-w-md p-8 text-center">
                  <Globe2 size={34} className="mx-auto text-cyanCore" />
                  <p className="mt-4 text-base font-medium text-textPrimary">Browser preview ready</p>
                  <p className="mt-2 text-sm leading-6 text-textSecondary">Run a task to launch a visible Playwright browser and stream screenshots back into Jarvis.</p>
                </div>
              )}
              <div className="absolute bottom-3 left-3 right-3 rounded-2xl border border-line bg-[#070B14]/85 px-3 py-2 backdrop-blur-xl">
                <p className="text-sm text-textPrimary">{browser.currentAction || "Ready"}</p>
              </div>
            </div>
          </div>

          <aside className="min-h-0 overflow-auto border-l border-line p-3">
            <h3 className="mb-3 text-base font-semibold text-textPrimary">DOM Understanding</h3>
            <div className="space-y-3">
              {domItems.map(([label, items, Icon]) => (
                <div key={label} className="rounded-2xl border border-line bg-white/[0.025] p-3">
                  <div className="mb-2 flex items-center gap-2">
                    <Icon size={15} className="text-cyanCore" />
                    <p className="text-sm font-medium text-textPrimary">{label}</p>
                  </div>
                  <div className="space-y-1">
                    {items.length ? (
                      items.slice(0, 6).map((item, index) => (
                        <p key={`${label}-${item}-${index}`} className="truncate text-xs text-textSecondary">{item}</p>
                      ))
                    ) : (
                      <p className="text-xs text-textSecondary">None detected yet.</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </aside>
        </div>
      </section>

      <aside className="grid gap-3">
        <section className="panel shrink-0 rounded-[24px] p-4">
          <h3 className="mb-3 text-base font-semibold text-textPrimary">Quick Visual Tasks</h3>
          <div className="grid gap-2">
            {quickTasks.map((item) => (
              <button
                key={item}
                type="button"
                disabled={!runtime.backendOnline || running}
                onClick={() => {
                  setTask(item);
                  runtime.runBrowserFlow(item);
                }}
                className="w-full rounded-2xl border border-line bg-white/[0.025] px-3 py-2 text-left text-sm text-textSecondary transition hover:text-textPrimary disabled:opacity-45"
              >
                {item}
              </button>
            ))}
          </div>
        </section>

        <section className="panel flex max-h-96 min-h-0 flex-col rounded-[24px] p-4">
          <h3 className="mb-3 text-base font-semibold text-textPrimary">Browser Logs</h3>
          <div className="min-h-0 flex-1 space-y-2 overflow-auto pr-1">
            {(browser.logs || []).length ? (
              browser.logs.map((log) => (
                <div key={log.id} className="rounded-2xl border border-line bg-white/[0.025] p-3">
                  <div className="mb-1 flex items-center justify-between gap-2">
                    <span className={`text-xs font-semibold capitalize ${log.level === "error" ? "text-red-200" : log.level === "warning" ? "text-amber-200" : "text-cyanCore"}`}>{log.level}</span>
                    <span className="text-[11px] text-textSecondary">{new Date(log.createdAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
                  </div>
                  <p className="text-sm text-textPrimary">{log.message}</p>
                </div>
              ))
            ) : (
              <p className="rounded-2xl border border-line bg-white/[0.025] p-3 text-sm text-textSecondary">No browser actions yet.</p>
            )}
          </div>
        </section>

        <section className="panel max-h-40 shrink-0 overflow-hidden rounded-[24px] p-4">
          <h3 className="mb-3 text-base font-semibold text-textPrimary">Tabs</h3>
          <div className="max-h-28 space-y-2 overflow-auto pr-1">
            {(browser.tabs || []).length ? (
              browser.tabs.map((tab) => (
                <div key={`${tab.index}-${tab.url}`} className="rounded-2xl border border-line bg-white/[0.025] p-3">
                  <p className="truncate text-sm text-textPrimary">{tab.index}. {tab.title || "Untitled"}</p>
                  <p className="mt-1 truncate text-xs text-textSecondary">{tab.url}</p>
                </div>
              ))
            ) : (
              <p className="rounded-2xl border border-line bg-white/[0.025] p-3 text-sm text-textSecondary">No tabs open yet.</p>
            )}
          </div>
        </section>
      </aside>
    </div>
  );
}

function ControlButton({ icon: Icon, label, disabled, onClick, danger = false }) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={`inline-flex h-10 items-center gap-2 rounded-2xl border px-3 text-sm transition disabled:opacity-40 ${
        danger ? "border-red-400/20 text-red-200 hover:bg-red-400/10" : "border-line text-textSecondary hover:text-textPrimary"
      }`}
    >
      <Icon size={15} />
      {label}
    </button>
  );
}
