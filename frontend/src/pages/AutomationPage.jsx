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

export default function AutomationPage() {
  const runtime = useOutletContext();
  const [task, setTask] = useState("open downloads and show system status");
  const [plan, setPlan] = useState([]);

  async function previewPlan() {
    const result = await runtime.previewPlanFlow(task);
    setPlan(result.plan || []);
  }

  return (
    <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_380px]">
      <section className="panel rounded-[28px] p-6">
        <div className="mb-6">
          <h2 className="text-2xl font-semibold tracking-[-0.03em] text-textPrimary">Automation</h2>
          <p className="mt-1 text-sm text-textSecondary">Autonomous task planning, safe desktop actions, and live execution logs.</p>
        </div>

        <div className="rounded-[24px] border border-line bg-white/[0.025] p-4">
          <label className="text-sm font-medium text-textPrimary" htmlFor="automation-task">Describe a workflow</label>
          <textarea
            id="automation-task"
            value={task}
            onChange={(event) => setTask(event.target.value)}
            className="mt-3 min-h-32 w-full resize-none rounded-2xl border border-line bg-[#070B14]/70 p-4 text-textPrimary outline-none placeholder:text-textSecondary"
            placeholder="Example: open downloads, create a note, search Google for React tutorials"
          />
          <div className="mt-3 flex flex-wrap gap-2">
            <button
              type="button"
              disabled={!runtime.backendOnline || runtime.busy || !task.trim()}
              onClick={previewPlan}
              className="inline-flex h-12 items-center gap-3 rounded-2xl border border-line bg-white/[0.035] px-4 text-sm font-medium text-textPrimary disabled:opacity-40"
            >
              <ListChecks size={17} />
              Plan
            </button>
            <button
              type="button"
              disabled={!runtime.backendOnline || runtime.busy || !task.trim()}
              onClick={() => runtime.runTextFlow(task, { agent: true })}
              className="inline-flex h-12 items-center gap-3 rounded-2xl bg-cyanCore px-4 text-sm font-semibold text-[#021018] disabled:opacity-40"
            >
              <Play size={17} />
              Execute
            </button>
            <button
              type="button"
              onClick={runtime.pauseAgentFlow}
              className="inline-flex h-12 items-center gap-3 rounded-2xl border border-line bg-white/[0.035] px-4 text-sm text-textSecondary"
            >
              <Pause size={17} />
              Pause
            </button>
            <button
              type="button"
              onClick={runtime.cancelAgentFlow}
              className="inline-flex h-12 items-center gap-3 rounded-2xl border border-line bg-white/[0.035] px-4 text-sm text-textSecondary"
            >
              <Square size={17} />
              Cancel
            </button>
            <button
              type="button"
              onClick={runtime.resumeAgentFlow}
              className="inline-flex h-12 items-center gap-3 rounded-2xl border border-line bg-white/[0.035] px-4 text-sm text-textSecondary"
            >
              <RotateCcw size={17} />
              Resume
            </button>
          </div>
        </div>

        {plan.length ? (
          <div className="mt-5 rounded-[24px] border border-line bg-white/[0.025] p-4">
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

        <div className="mt-6">
          <h3 className="mb-3 text-base font-semibold text-textPrimary">Execution logs</h3>
          <ExecutionLogs logs={runtime.executionLogs} />
        </div>
      </section>

      <aside className="space-y-4">
        <section className="panel rounded-[28px] p-5">
          <h3 className="mb-4 text-base font-semibold text-textPrimary">Live thinking</h3>
          <ThinkingTimeline items={runtime.thinkingTimeline} compact />
        </section>

        <WorkflowRecorder runtime={runtime} />

        <section className="panel rounded-[28px] p-5">
          <div className="mb-4 flex items-center gap-2">
            <Workflow size={17} className="text-cyanCore" />
            <h3 className="text-base font-semibold text-textPrimary">AI routines</h3>
          </div>
          <div className="space-y-2">
            {routines.map((routine) => (
              <button
                key={routine}
                type="button"
                onClick={() => setTask(routine)}
                className="w-full rounded-2xl border border-line bg-white/[0.025] p-3 text-left text-sm text-textSecondary transition hover:text-textPrimary"
              >
                {routine}
              </button>
            ))}
          </div>
        </section>

        <section className="panel rounded-[28px] p-5">
          <div className="mb-4 flex items-center gap-2">
            <AppWindow size={17} className="text-cyanCore" />
            <h3 className="text-base font-semibold text-textPrimary">Desktop apps</h3>
          </div>
          <div className="space-y-2">
            {runtime.installedApps.slice(0, 8).map((app) => (
              <button
                key={app.id}
                type="button"
                onClick={() => runtime.runTextFlow(`open ${app.label}`, { agent: true })}
                className="flex w-full items-center justify-between rounded-2xl border border-line bg-white/[0.025] p-3 text-left text-sm transition hover:border-cyanCore/40"
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
