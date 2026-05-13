export default function WorkflowDesigner({ workflows = [] }) {
  return (
    <div className="grid gap-2">
      {workflows.map((workflow) => (
        <div key={workflow.id || workflow.name} className="rounded-2xl border border-line bg-white/[0.025] px-3 py-2">
          <p className="text-sm font-medium text-textPrimary">{workflow.name || "Workflow"}</p>
          <p className="text-xs text-textSecondary">{workflow.nodes?.length || 0} node(s)</p>
        </div>
      ))}
    </div>
  );
}
