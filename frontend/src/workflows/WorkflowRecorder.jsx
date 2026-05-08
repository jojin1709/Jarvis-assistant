import { Play, Radio, RotateCcw, Square } from "lucide-react";
import { useState } from "react";

export default function WorkflowRecorder({ runtime }) {
  const [name, setName] = useState("My Jarvis workflow");
  const recorder = runtime.workflowRecorder || { active: false, workflows: [] };

  return (
    <section className="panel rounded-[28px] p-5">
      <div className="mb-4 flex items-center gap-2">
        <Radio size={17} className="text-cyanCore" />
        <h3 className="text-base font-semibold text-textPrimary">Workflow recorder</h3>
      </div>

      <div className="rounded-2xl border border-line bg-white/[0.025] p-3">
        <input
          value={name}
          onChange={(event) => setName(event.target.value)}
          className="h-10 w-full rounded-xl border border-line bg-[#070B14]/70 px-3 text-sm text-textPrimary outline-none"
          placeholder="Workflow name"
          disabled={recorder.active}
        />
        <div className="mt-3 flex gap-2">
          <button
            type="button"
            disabled={recorder.active}
            onClick={() => runtime.startWorkflowRecordingFlow(name)}
            className="inline-flex h-10 flex-1 items-center justify-center gap-2 rounded-xl bg-cyanCore px-3 text-sm font-semibold text-[#021018] disabled:opacity-40"
          >
            <Play size={15} />
            Record
          </button>
          <button
            type="button"
            disabled={!recorder.active}
            onClick={runtime.stopWorkflowRecordingFlow}
            className="inline-flex h-10 flex-1 items-center justify-center gap-2 rounded-xl border border-line bg-white/[0.035] px-3 text-sm font-medium text-textPrimary disabled:opacity-40"
          >
            <Square size={15} />
            Stop
          </button>
        </div>
      </div>

      <div className="mt-4 space-y-2">
        {(recorder.workflows || []).slice(0, 5).map((workflow) => (
          <button
            key={workflow.id}
            type="button"
            onClick={() => runtime.replayWorkflowFlow(workflow.id)}
            className="flex w-full items-center justify-between rounded-2xl border border-line bg-white/[0.025] p-3 text-left text-sm transition hover:border-cyanCore/40"
          >
            <span>
              <span className="block font-medium text-textPrimary">{workflow.name}</span>
              <span className="text-textSecondary">{workflow.actionCount} action(s)</span>
            </span>
            <RotateCcw size={15} className="text-textSecondary" />
          </button>
        ))}
      </div>
    </section>
  );
}
