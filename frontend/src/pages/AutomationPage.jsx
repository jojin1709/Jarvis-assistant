import { useState } from "react";
import { useOutletContext } from "react-router-dom";
import { AppWindow, ListChecks, Pause, Play, RotateCcw, Square, Workflow } from "lucide-react";

import ExecutionLogs from "../components/ExecutionLogs.jsx";
import ThinkingTimeline from "../widgets/ThinkingTimeline.jsx";
import WorkflowRecorder from "../workflows/WorkflowRecorder.jsx";

const routines = [
  "Open VS Code and latest project",
  "Create a note and list desktop",
  "Search Google for today's AI news",
];

const appCommandLabels = {
  "File Explorer": "open file explorer",
  "VS Code": "open vs code",
};

export default function AutomationPage() {
  const runtime = useOutletContext();
  const [task, setTask] = useState("open downloads and show system status");
  const [plan, setPlan] = useState([]);
  const control = runtime.executionControl || {};
  const canPause = runtime.backendOnline && !control.paused && !control.cancelled && ["executing", "coding"].includes(runtime.mode);
  const canResume = runtime.backendOnline && Boolean(control.paused);
  const canCancel = runtime.backendOnline && !control.cancelled && ["executing", "coding"].includes(runtime.mode);

  async function previewPlan() {
    try {
      const result = await runtime.previewPlanFlow(task);
      setPlan(result.plan || []);
    } catch (error) {
      runtime.addExecutionLog({ message: error?.message || "Plan failed", level: "error" });
    }
  }

  async function executeWorkflow(nextTask = task) {
    const command = nextTask.trim();
    if (!command) return;
    try {
      const result = await runtime.runTextFlow(command, { agent: true });
      setPlan(result?.plan || []);
    } catch {
      // The runtime already records the failure in the response and logs.
    }
  }

  function appCommand(app) {
    return appCommandLabels[app.label] || `open ${app.label}`;
  }

  return (
    <div className="grid min-h-full gap-3 xl:grid-cols-[minmax(0,1fr)_360px]">
      <section className="panel flex min-h-0 flex-col rounded-[24px] p-4">
        <div className="mb-3 shrink-0">
          <h2 className="text-xl font-semibold tracking-[-0.03em] text-textPrimary">Automation</h2>
          <p className="mt-1 text-sm text-textSecondary">Autonomous task planning, safe desktop actions, and live execution logs.</p>
        </div>

        <div className="shrink-0 rounded-[22px] border border-line bg-white/[0.025] p-3">
          <label className="text-sm font-medium text-textPrimary" htmlFor="automation-task">Describe a workflow</label>
          <textarea
            id="automation-task"
            value={task}
            onChange={(event) => setTask(event.target.value)}
            className="mt-2 min-h-14 w-full resize-none rounded-2xl border border-line bg-[#070B14]/70 p-3 text-sm text-textPrimary outline-none placeholder:text-textSecondary"
            placeholder="Example: open downloads, create a note, search Google for React tutorials"
          />
          <div className="mt-3 flex flex-wrap gap-2">
            <button
              type="button"
              disabled={!runtime.backendOnline || runtime.busy || !task.trim()}
              onClick={previewPlan}
              className="inline-flex h-10 items-center gap-2 rounded-2xl border border-line bg-white/[0.035] px-3 text-sm font-medium text-textPrimary disabled:opacity-40"
            >
              <ListChecks size={17} />
              Plan
            </button>
            <button
              type="button"
              disabled={!runtime.backendOnline || runtime.busy || !task.trim()}
              onClick={() => executeWorkflow()}
              className="inline-flex h-10 items-center gap-2 rounded-2xl bg-cyanCore px-3 text-sm font-semibold text-[#021018] disabled:opacity-40"
            >
              <Play size={17} />
              Execute
            </button>
            <button
              type="button"
              onClick={runtime.pauseAgentFlow}
              disabled={!canPause}
              className="inline-flex h-10 items-center gap-2 rounded-2xl border border-line bg-white/[0.035] px-3 text-sm text-textSecondary disabled:cursor-not-allowed disabled:opacity-40"
            >
              <Pause size={17} />
              Pause
            </button>
            <button
              type="button"
              onClick={runtime.cancelAgentFlow}
              disabled={!canCancel}
              className="inline-flex h-10 items-center gap-2 rounded-2xl border border-line bg-white/[0.035] px-3 text-sm text-textSecondary disabled:cursor-not-allowed disabled:opacity-40"
            >
              <Square size={17} />
              Cancel
            </button>
            <button
              type="button"
              onClick={runtime.resumeAgentFlow}
              disabled={!canResume}
              className="inline-flex h-10 items-center gap-2 rounded-2xl border border-line bg-white/[0.035] px-3 text-sm text-textSecondary disabled:cursor-not-allowed disabled:opacity-40"
            >
              <RotateCcw size={17} />
              Resume
            </button>
          </div>
        </div>

        {plan.length ? (
          <div className="mt-3 shrink-0 rounded-[22px] border border-line bg-white/[0.025] p-3">
            <h3 className="mb-3 text-base font-semibold text-textPrimary">Execution plan</h3>
            <div className="space-y-2">
              {plan.map((step, index) => (
                <div key={`${step.label}-${index}`} className="flex items-center justify-between rounded-2xl bg-white/[0.025] p-3 text-sm">
                  <span className="text-textPrimary">{index + 1}. {step.label}</span>
                  <span className="rounded-full bg-white/[0.055] px-2 py-0.5 text-xs text-textSecondary">{step.risk} risk</span>
                </div>
              ))}
            </div>
          </div>
        ) : null}

        <div className="mt-3 flex min-h-0 flex-1 flex-col">
          <h3 className="mb-3 text-base font-semibold text-textPrimary">Execution logs</h3>
          <div className="min-h-0 flex-1 overflow-auto pr-1">
            <ExecutionLogs logs={runtime.executionLogs} />
          </div>
        </div>
      </section>

      <aside className="grid gap-3">
        <section className="panel rounded-[24px] p-4">
          <h3 className="mb-3 text-base font-semibold text-textPrimary">Live thinking</h3>
          <ThinkingTimeline items={runtime.thinkingTimeline} compact />
        </section>

        <WorkflowRecorder runtime={runtime} />

        <section className="panel rounded-[24px] p-4">
          <div className="mb-4 flex items-center gap-2">
            <Workflow size={17} className="text-cyanCore" />
            <h3 className="text-base font-semibold text-textPrimary">AI routines</h3>
          </div>
          <div className="space-y-2">
            {routines.map((routine) => (
              <div key={routine} className={`flex items-center gap-2 rounded-2xl border bg-white/[0.025] p-2 transition ${task === routine ? "border-cyanCore/35" : "border-line"}`}>
                <button
                  type="button"
                  disabled={runtime.busy}
                  onClick={() => setTask(routine)}
                  className="min-w-0 flex-1 rounded-xl px-2 py-2 text-left text-sm text-textSecondary transition hover:text-textPrimary disabled:cursor-not-allowed disabled:opacity-40"
                >
                  <span className="block truncate">{routine}</span>
                </button>
                <button
                  type="button"
                  disabled={!runtime.backendOnline || runtime.busy}
                  onClick={() => {
                    setTask(routine);
                    executeWorkflow(routine);
                  }}
                  className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-cyanCore text-[#021018] transition hover:bg-cyanSoft disabled:cursor-not-allowed disabled:opacity-40"
                  title="Run routine"
                >
                  <Play size={15} />
                </button>
              </div>
            ))}
          </div>
        </section>

        <section className="panel rounded-[24px] p-4">
          <div className="mb-4 flex items-center gap-2">
            <AppWindow size={17} className="text-cyanCore" />
            <h3 className="text-base font-semibold text-textPrimary">Desktop apps</h3>
          </div>
          <div className="max-h-72 space-y-2 overflow-auto pr-1">
            {runtime.installedApps.slice(0, 8).map((app) => (
              <button
                key={app.id}
                type="button"
                disabled={!runtime.backendOnline || runtime.busy}
                onClick={() => runtime.runTextFlow(appCommand(app))}
                className="flex w-full items-center justify-between rounded-2xl border border-line bg-white/[0.025] p-3 text-left text-sm transition hover:border-cyanCore/40 disabled:cursor-not-allowed disabled:opacity-40"
              >
                <span className="text-textPrimary">{app.label}</span>
                <span className={app.running ? "text-cyanCore" : app.installed ? "text-textSecondary" : "text-amber-300"}>
                  {app.running ? "Running" : app.installed ? "Ready" : "Web fallback"}
                </span>
              </button>
            ))}
          </div>
        </section>
      </aside>
    </div>
  );
}
