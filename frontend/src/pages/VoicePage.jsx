import { useOutletContext } from "react-router-dom";
import { Mic2, Power, Radio } from "lucide-react";

import Waveform from "../components/Waveform.jsx";

export default function VoicePage() {
  const runtime = useOutletContext();

  return (
    <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_360px]">
      <section className="panel rounded-[28px] p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h2 className="text-2xl font-semibold tracking-[-0.03em] text-textPrimary">Voice</h2>
            <p className="mt-1 text-sm text-textSecondary">Speech-to-text, wake word status, waveform, and voice history.</p>
          </div>
          <button
            type="button"
            disabled={!runtime.backendOnline || runtime.busy}
            onClick={runtime.runVoiceFlow}
            className="inline-flex h-12 items-center gap-3 rounded-2xl bg-cyanCore px-4 text-sm font-semibold text-[#021018] disabled:opacity-40"
          >
            <Mic2 size={18} />
            Start listening
          </button>
        </div>

        <div className="mt-8">
          <Waveform active={runtime.activeWave} />
        </div>

        <div className="mt-6 grid gap-3 sm:grid-cols-3">
          <VoiceCard icon={Radio} label="Wake word" value={runtime.wakeEnabled ? "Enabled" : "Disabled"} />
          <VoiceCard icon={Power} label="Mode" value={runtime.mode} />
          <VoiceCard icon={Mic2} label="Language" value={runtime.languageMode} />
        </div>

        <div className="mt-6 rounded-[24px] border border-line bg-white/[0.025] p-4">
          <p className="text-sm text-textSecondary">Live transcript</p>
          <p className="mt-2 text-lg text-textPrimary">{runtime.transcript}</p>
        </div>
      </section>

      <aside className="panel rounded-[28px] p-5">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-base font-semibold text-textPrimary">Voice history</h3>
          <button
            type="button"
            onClick={() => runtime.setWakeEnabled(!runtime.wakeEnabled)}
            className="rounded-xl border border-line px-3 py-1.5 text-sm text-textSecondary hover:text-textPrimary"
          >
            Wake {runtime.wakeEnabled ? "on" : "off"}
          </button>
        </div>
        <div className="space-y-2">
          {runtime.voiceHistory.length ? (
            runtime.voiceHistory.map((item) => (
              <div key={item.id} className="rounded-2xl border border-line bg-white/[0.025] p-3">
                <p className="text-sm text-textPrimary">{item.transcript}</p>
                <p className="mt-1 text-xs text-textSecondary">{item.response}</p>
              </div>
            ))
          ) : (
            <p className="rounded-2xl border border-line bg-white/[0.025] p-3 text-sm text-textSecondary">No voice commands yet.</p>
          )}
        </div>
      </aside>
    </div>
  );
}

function VoiceCard({ icon: Icon, label, value }) {
  return (
    <div className="rounded-2xl border border-line bg-white/[0.025] p-4">
      <Icon size={18} className="text-cyanCore" />
      <p className="mt-3 text-sm text-textSecondary">{label}</p>
      <p className="mt-1 font-medium capitalize text-textPrimary">{value}</p>
    </div>
  );
}
