import { useState } from "react";
import { useOutletContext } from "react-router-dom";
import { Mic2, Power, Radio, Trash2 } from "lucide-react";

import Waveform from "../components/Waveform.jsx";

export default function VoicePage() {
  const runtime = useOutletContext();
  const [confirmClear, setConfirmClear] = useState(false);

  function clearVoiceHistory() {
    if (!runtime.voiceHistory.length) return;
    if (!confirmClear) {
      setConfirmClear(true);
      return;
    }
    runtime.clearVoiceHistory();
    runtime.addExecutionLog({ message: "Voice history cleared", level: "warning" });
    setConfirmClear(false);
  }

  return (
    <div className="grid min-h-full gap-3 xl:grid-cols-[minmax(0,1fr)_340px]">
      <section className="panel flex min-h-0 flex-col overflow-hidden rounded-[24px] p-4">
        <div className="shrink-0 flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-xl font-semibold tracking-[-0.03em] text-textPrimary">Voice</h2>
            <p className="mt-1 text-sm text-textSecondary">Speech-to-text, wake word status, waveform, and voice history.</p>
          </div>
          <button
            type="button"
            disabled={!runtime.backendOnline || runtime.busy}
            onClick={runtime.runVoiceFlow}
            className="inline-flex h-10 items-center gap-2 rounded-2xl bg-cyanCore px-4 text-sm font-semibold text-[#021018] disabled:opacity-40"
          >
            <Mic2 size={18} />
            Start listening
          </button>
        </div>

        <div className="mt-4 shrink-0">
          <Waveform active={runtime.activeWave} />
        </div>

        <div className="mt-4 grid shrink-0 gap-3 sm:grid-cols-3">
          <VoiceCard icon={Radio} label="Wake word" value={runtime.wakeEnabled ? "Enabled" : "Disabled"} />
          <VoiceCard icon={Power} label="Mode" value={runtime.mode} />
          <VoiceCard icon={Mic2} label="Language" value={runtime.languageMode} />
        </div>

        <div className="mt-4 min-h-0 flex-1 rounded-[22px] border border-line bg-white/[0.025] p-3">
          <p className="text-sm text-textSecondary">Live transcript</p>
          <p className="mt-2 text-lg text-textPrimary">{runtime.transcript}</p>
        </div>
      </section>

      <aside className="panel flex min-h-0 flex-col rounded-[24px] p-4">
        <div className="mb-3 shrink-0 flex items-center justify-between gap-2">
          <h3 className="text-base font-semibold text-textPrimary">Voice history</h3>
          <div className="flex items-center gap-2">
            <button
              type="button"
              disabled={!runtime.voiceHistory.length}
              onClick={clearVoiceHistory}
              onBlur={() => setConfirmClear(false)}
              title={confirmClear ? "Confirm clear voice history" : "Clear voice history"}
              className={`grid h-10 w-10 place-items-center rounded-xl border text-sm transition disabled:cursor-not-allowed disabled:opacity-40 ${
                confirmClear
                  ? "border-red-400/30 bg-red-400/10 text-red-200 hover:bg-red-400/15"
                  : "border-line bg-white/[0.035] text-textSecondary hover:text-textPrimary"
              }`}
            >
              <Trash2 size={15} />
            </button>
            <button
              type="button"
              onClick={() => runtime.setWakeEnabled(!runtime.wakeEnabled)}
              className="rounded-xl border border-line px-3 py-1.5 text-sm text-textSecondary hover:text-textPrimary"
            >
              Wake {runtime.wakeEnabled ? "on" : "off"}
            </button>
          </div>
        </div>
        <div className="min-h-0 flex-1 space-y-2 overflow-auto pr-1">
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
    <div className="rounded-2xl border border-line bg-white/[0.025] p-3">
      <Icon size={18} className="text-cyanCore" />
      <p className="mt-2 text-sm text-textSecondary">{label}</p>
      <p className="mt-1 font-medium capitalize text-textPrimary">{value}</p>
    </div>
  );
}
