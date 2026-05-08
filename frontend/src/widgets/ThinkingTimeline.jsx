import { BrainCircuit, CheckCircle2, CircleDashed, RotateCcw, XCircle } from "lucide-react";

const iconMap = {
  success: CheckCircle2,
  error: XCircle,
  warning: RotateCcw,
  running: CircleDashed,
};

export default function ThinkingTimeline({ items = [], compact = false }) {
  const visible = items.slice(0, compact ? 5 : 10);

  return (
    <div className="space-y-3">
      {visible.length === 0 ? (
        <div className="rounded-2xl border border-line bg-white/[0.025] p-4 text-sm text-textSecondary">
          Waiting for Jarvis to think, plan, or execute.
        </div>
      ) : (
        visible.map((item) => {
          const Icon = iconMap[item.status] || BrainCircuit;
          return (
            <div key={item.id} className="rounded-2xl border border-line bg-white/[0.025] p-3">
              <div className="flex items-start gap-3">
                <div className="mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-cyanCore/10 text-cyanCore">
                  <Icon size={16} className={item.status === "running" ? "animate-spin" : ""} />
                </div>
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="text-sm font-medium capitalize text-textPrimary">{item.phase || "thinking"}</p>
                    {item.tool ? <span className="rounded-full bg-white/[0.055] px-2 py-0.5 text-[11px] text-textSecondary">{item.tool}</span> : null}
                  </div>
                  <p className="mt-1 text-sm text-textSecondary">{item.message}</p>
                </div>
              </div>
            </div>
          );
        })
      )}
    </div>
  );
}
