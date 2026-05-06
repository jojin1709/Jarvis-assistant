export default function CompactStatus({ mode, backendOnline, wakeEnabled, now }) {
  const time = now.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });

  return (
    <div className="flex items-center justify-between gap-3 rounded-full border border-cyanCore/20 bg-black/35 px-4 py-2 backdrop-blur">
      <div className="flex items-center gap-2">
        <span className={`h-2.5 w-2.5 rounded-full ${backendOnline ? "bg-emerald-300" : "bg-red-400"}`} />
        <span className="text-xs uppercase tracking-[0.18em] text-white/70">{backendOnline ? "Online" : "Offline"}</span>
      </div>
      <span className="text-xs uppercase tracking-[0.18em] text-cyanSoft/70">{mode}</span>
      <span className={`text-xs uppercase tracking-[0.18em] ${wakeEnabled ? "text-emerald-200" : "text-white/35"}`}>
        Wake {wakeEnabled ? "On" : "Off"}
      </span>
      <span className="font-display text-sm text-cyanSoft">{time}</span>
    </div>
  );
}
