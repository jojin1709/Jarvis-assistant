import { Cpu, Radio, ShieldCheck, Wifi } from "lucide-react";

const statusRows = [
  { label: "Core", icon: Cpu },
  { label: "Voice", icon: Radio },
  { label: "Link", icon: Wifi },
  { label: "Guard", icon: ShieldCheck },
];

export default function StatusPanel({ mode, backendOnline }) {
  return (
    <section className="hud-panel p-5">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-[0.28em] text-cyanSoft">Systems</h2>
        <span className={`h-2.5 w-2.5 rounded-full ${backendOnline ? "bg-emerald-300" : "bg-red-400"}`} />
      </div>

      <div className="space-y-3">
        {statusRows.map(({ label, icon: Icon }, index) => (
          <div key={label} className="flex items-center justify-between border-b border-cyanCore/10 pb-2 last:border-0">
            <div className="flex items-center gap-3 text-cyanSoft/85">
              <Icon size={18} />
              <span className="text-sm uppercase tracking-[0.18em]">{label}</span>
            </div>
            <span className="text-sm text-white/80">{index === 2 && !backendOnline ? "offline" : "nominal"}</span>
          </div>
        ))}
      </div>

      <div className="mt-5 border border-cyanCore/20 bg-black/25 p-3">
        <p className="text-xs uppercase tracking-[0.22em] text-cyanSoft/70">Mode</p>
        <p className="mt-1 text-xl font-semibold uppercase text-white">{mode}</p>
      </div>
    </section>
  );
}
