import { BrainCircuit, Cpu, DatabaseZap, Radio } from "lucide-react";

import MicButton from "./MicButton.jsx";
import Orb from "./Orb.jsx";
import Waveform from "./Waveform.jsx";

const telemetry = [
  { label: "Neural", value: "Synced", icon: BrainCircuit },
  { label: "Runtime", value: "Local", icon: Cpu },
  { label: "Memory", value: "Ready", icon: DatabaseZap },
  { label: "Signal", value: "Clear", icon: Radio },
];

export default function CoreStage({ mode, activeWave, backendOnline, busy, onVoice }) {
  return (
    <section className="relative overflow-hidden rounded-[2rem] border border-cyanCore/25 bg-black/30 shadow-panel">
      <div className="absolute inset-0 reactor-field" />
      <div className="absolute left-5 right-5 top-5 grid grid-cols-2 gap-2 sm:grid-cols-4">
        {telemetry.map(({ label, value, icon: Icon }) => (
          <div key={label} className="flex items-center justify-center gap-2 border border-cyanCore/20 bg-black/35 px-2 py-2">
            <Icon size={15} className="text-cyanSoft" />
            <span className="text-[10px] uppercase tracking-[0.15em] text-cyanSoft/55">{label}</span>
            <span className="text-[10px] uppercase tracking-[0.15em] text-white/75">{value}</span>
          </div>
        ))}
      </div>

      <div className="relative z-10 flex min-h-[520px] flex-col items-center justify-center px-5 pb-9 pt-20">
        <div className="relative w-full max-w-[320px]">
          <Orb mode={mode} />
        </div>

        <div className="mt-2 w-full max-w-md">
          <Waveform active={activeWave} />
        </div>

        <div className="mt-9 flex justify-center pb-8">
          <MicButton disabled={!backendOnline || busy} active={busy} onClick={onVoice} />
        </div>
      </div>
    </section>
  );
}
