import { useNavigate, useOutletContext } from "react-router-dom";
import { Camera, CheckCircle2, FolderOpen, Mic2, Plug, Sparkles } from "lucide-react";

import CoreStage from "../components/CoreStage.jsx";
import ExecutionLogs from "../components/ExecutionLogs.jsx";
import QuickDock from "../components/QuickDock.jsx";
import ThinkingTimeline from "../widgets/ThinkingTimeline.jsx";

const suggestions = ["open Sarvam dashboard", "open downloads", "search google for latest AI tools", "what do you remember"];

export default function HomePage() {
  const runtime = useOutletContext();
  const navigate = useNavigate();

  return (
    <div className="grid min-h-full grid-cols-1 gap-3 xl:grid-cols-[minmax(0,1fr)_380px]">
      <div className="flex min-w-0 flex-col gap-3">
        <CoreStage
          mode={runtime.mode}
          activeWave={runtime.activeWave}
          backendOnline={runtime.backendOnline}
          busy={runtime.busy}
          onVoice={runtime.runVoiceFlow}
        />

        <section className="panel shrink-0 rounded-[24px] p-4">
          <div className="mb-3 flex items-center justify-between">
            <div>
              <h2 className="text-base font-semibold text-textPrimary">Quick commands</h2>
              <p className="text-sm text-textSecondary">Frequent actions for fast desktop work.</p>
            </div>
          </div>
          <QuickDock
            disabled={!runtime.backendOnline || runtime.busy}
            wakeEnabled={runtime.wakeEnabled}
            onRun={runtime.runAction}
            onToggleWake={() => runtime.setWakeEnabled(!runtime.wakeEnabled)}
            onUploadClick={() => navigate("/files")}
          />
        </section>
      </div>

      <aside className="flex min-w-0 flex-col gap-3">
        <section className="panel rounded-[24px] p-4">
          <h2 className="mb-3 text-base font-semibold text-textPrimary">System overview</h2>
          <div className="grid gap-2">
            <Status icon={CheckCircle2} label="Assistant" value={runtime.backendOnline ? "Online" : "Offline"} />
            <Status icon={Mic2} label="Voice" value={runtime.wakeEnabled ? "Wake enabled" : "Push-to-talk"} />
            <Status icon={FolderOpen} label="Files" value={`${runtime.uploads.length} recent upload(s)`} />
            <Status icon={Sparkles} label="Memory" value={`${runtime.memory?.memory_count || 0} saved item(s)`} />
            <Status icon={Plug} label="Skills" value={`${runtime.plugins?.filter((plugin) => plugin.enabled).length || 0} active plugin(s)`} />
          </div>
        </section>

        <section className="panel rounded-[24px] p-4">
          <div className="mb-2 flex items-center justify-between gap-3">
            <h2 className="text-base font-semibold text-textPrimary">Screen intelligence</h2>
            <button
              type="button"
              onClick={runtime.captureVisionFlow}
              disabled={!runtime.backendOnline || runtime.busy}
              className="grid h-9 w-9 place-items-center rounded-xl border border-line bg-white/[0.035] text-textSecondary hover:text-textPrimary disabled:cursor-not-allowed disabled:opacity-45"
            >
              <Camera size={16} />
            </button>
          </div>
          <p className="line-clamp-2 text-sm text-textSecondary">
            {runtime.vision?.summary || "Capture the screen to let Jarvis inspect visible UI state."}
          </p>
        </section>

        <section className="panel rounded-[24px] p-4">
          <h2 className="mb-3 text-base font-semibold text-textPrimary">Live thinking</h2>
          <div className="max-h-40 overflow-auto pr-1">
            <ThinkingTimeline items={runtime.thinkingTimeline} compact />
          </div>
        </section>

        <section className="panel rounded-[24px] p-4">
          <h2 className="mb-3 text-base font-semibold text-textPrimary">Smart suggestions</h2>
          <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-1 2xl:grid-cols-2">
            {suggestions.map((suggestion) => (
              <button
                key={suggestion}
                type="button"
                disabled={!runtime.backendOnline || runtime.busy}
                onClick={() => runtime.runTextFlow(suggestion)}
                className="w-full rounded-2xl border border-line bg-white/[0.025] px-3 py-2 text-left text-sm text-textSecondary transition hover:bg-white/[0.055] hover:text-textPrimary disabled:opacity-45"
              >
                {suggestion}
              </button>
            ))}
          </div>
        </section>

        <section className="panel rounded-[24px] p-4">
          <h2 className="mb-3 text-base font-semibold text-textPrimary">Execution logs</h2>
          <ExecutionLogs logs={runtime.executionLogs} compact />
        </section>
      </aside>
    </div>
  );
}

function Status({ icon: Icon, label, value }) {
  return (
    <div className="rounded-2xl border border-line bg-white/[0.025] px-3 py-2">
      <div className="flex items-center gap-3">
        <div className="grid h-8 w-8 place-items-center rounded-xl bg-cyanCore/10 text-cyanCore">
          <Icon size={16} />
        </div>
        <div>
          <p className="text-sm font-medium text-textPrimary">{label}</p>
          <p className="text-sm text-textSecondary">{value}</p>
        </div>
      </div>
    </div>
  );
}
