import { Cpu, Mic2, ShieldCheck, Wifi } from "lucide-react";

const statusRows = [
  { label: "Runtime", icon: Cpu },
  { label: "Voice", icon: Mic2 },
  { label: "Connection", icon: Wifi },
  { label: "Security", icon: ShieldCheck },
];

export default function StatusPanel({ mode, backendOnline }) {
  return (
    <section className="panel rounded-[28px] p-5">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-base font-semibold text-textPrimary">System status</h2>
        <span className={`h-2.5 w-2.5 rounded-full ${backendOnline ? "bg-emerald-400" : "bg-red-400"}`} />
      </div>

      <div className="space-y-3">
        {statusRows.map(({ label, icon: Icon }, index) => (
          <div key={label} className="flex items-center justify-between border-b border-line pb-2 last:border-0">
            <div className="flex items-center gap-3 text-textSecondary">
              <Icon size={17} />
              <span className="text-sm">{label}</span>
            </div>
            <span className="text-sm text-textPrimary">{index === 2 && !backendOnline ? "Offline" : "Ready"}</span>
          </div>
        ))}
      </div>

      <div className="mt-5 rounded-2xl border border-line bg-white/[0.03] p-3">
        <p className="text-sm text-textSecondary">Mode</p>
        <p className="mt-1 text-lg font-semibold text-textPrimary">{mode.charAt(0).toUpperCase() + mode.slice(1)}</p>
      </div>
    </section>
  );
}
