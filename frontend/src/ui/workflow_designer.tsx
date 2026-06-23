import { useEffect, useState } from "react";

interface Workflow {
  id?: string;
  name?: string;
  nodes?: unknown[];
  steps?: unknown[];
  updatedAt?: string;
}

export default function WorkflowDesigner({ workflows: propWorkflows = [] }: { workflows?: Workflow[] }) {
  const [workflows, setWorkflows] = useState<Workflow[]>(propWorkflows);
  const [loading, setLoading] = useState(propWorkflows.length === 0);
  const [runningId, setRunningId] = useState("");

  useEffect(() => {
    if (propWorkflows.length > 0) {
      setWorkflows(propWorkflows);
      setLoading(false);
      return;
    }

    let active = true;
    fetch("/api/workflows/graphs")
      .then((response) => response.json())
      .then((data) => {
        if (active) setWorkflows(data.workflows || []);
      })
      .catch(() => {})
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [propWorkflows]);

  async function runWorkflow(workflow: Workflow) {
    if (!workflow.id) return;
    setRunningId(workflow.id);
    try {
      await fetch(`/api/workflows/graphs/${encodeURIComponent(workflow.id)}/run`, { method: "POST" });
    } finally {
      setRunningId("");
    }
  }

  if (loading) return <div className="h-12 animate-pulse rounded-xl bg-white/5" />;

  if (!workflows.length) {
    return <p className="py-4 text-center text-sm text-textSecondary">No workflow graphs yet.</p>;
  }

  return (
    <div className="grid gap-2">
      {workflows.map((workflow) => (
        <div key={workflow.id || workflow.name} className="flex items-center justify-between gap-3 rounded-2xl border border-line bg-white/[0.025] px-3 py-2">
          <div className="min-w-0">
            <p className="truncate text-sm font-medium text-textPrimary">{workflow.name || workflow.id || "Workflow"}</p>
            <p className="text-xs text-textSecondary">{workflow.nodes?.length || workflow.steps?.length || 0} node(s)</p>
          </div>
          <button
            type="button"
            disabled={!workflow.id || runningId === workflow.id}
            onClick={() => runWorkflow(workflow)}
            className="rounded-xl border border-cyanCore/30 px-3 py-1 text-xs font-medium text-cyanCore disabled:cursor-not-allowed disabled:opacity-40"
          >
            {runningId === workflow.id ? "Running" : "Run"}
          </button>
        </div>
      ))}
    </div>
  );
}
