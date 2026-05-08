import { CheckCircle2, Circle, Loader2, XCircle } from "lucide-react";

const icons = {
  success: CheckCircle2,
  error: XCircle,
  running: Loader2,
  info: Circle,
};

export default function ExecutionLogs({ logs = [], compact = false }) {
  const visible = logs.slice(0, compact ? 5 : 40);

  return (
    <div className="space-y-2">
      {visible.length ? (
        visible.map((log) => {
          const Icon = icons[log.level] || Circle;
          return (
            <div key={log.id || `${log.createdAt}-${log.message}`} className="rounded-2xl border border-line bg-white/[0.025] p-3">
              <div className="flex items-start gap-3">
                <Icon
                  size={16}
                  className={`mt-0.5 shrink-0 ${
                    log.level === "success"
                      ? "text-emerald-400"
                      : log.level === "error"
                        ? "text-red-400"
                        : log.level === "running"
                          ? "animate-spin text-cyanCore"
                          : "text-textSecondary"
                  }`}
                />
                <div className="min-w-0">
                  <p className="text-sm text-textPrimary">{log.message}</p>
                  {log.createdAt && <p className="mt-1 text-xs text-textSecondary">{new Date(log.createdAt).toLocaleTimeString()}</p>}
                </div>
              </div>
            </div>
          );
        })
      ) : (
        <p className="rounded-2xl border border-line bg-white/[0.025] p-3 text-sm text-textSecondary">No execution logs yet.</p>
      )}
    </div>
  );
}
