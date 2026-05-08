export default function CompactStatus({ mode, backendOnline, wakeEnabled, now }) {
  const time = now.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
  const modeLabel = mode.charAt(0).toUpperCase() + mode.slice(1);

  return (
    <div className="flex items-center gap-3 rounded-2xl border border-line bg-white/[0.035] px-3 py-2">
      <div className="flex items-center gap-2">
        <span className={`h-2 w-2 rounded-full ${backendOnline ? "bg-emerald-400" : "bg-red-400"}`} />
        <span className="text-sm font-medium text-textPrimary">{backendOnline ? "Online" : "Offline"}</span>
      </div>
      <span className="hidden h-4 w-px bg-white/10 sm:block" />
      <span className="text-sm text-textSecondary">{modeLabel}</span>
      <span className={`hidden text-sm sm:inline ${wakeEnabled ? "text-emerald-300" : "text-textSecondary"}`}>
        Wake {wakeEnabled ? "on" : "off"}
      </span>
      <span className="text-sm tabular-nums text-textSecondary">{time}</span>
    </div>
  );
}
