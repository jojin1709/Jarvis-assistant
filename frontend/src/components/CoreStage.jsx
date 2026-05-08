import { AnimatePresence, motion } from "framer-motion";
import { Bot, CheckCircle2, Mic2, Sparkles } from "lucide-react";

import MicButton from "./MicButton.jsx";
import Waveform from "./Waveform.jsx";

const suggestions = [
  "Open Sarvam dashboard",
  "Search Google for React desktop apps",
  "Open downloads",
  "What do you remember?",
];

export default function CoreStage({ mode, activeWave, backendOnline, busy, onVoice, onSuggestion }) {
  const modeText = mode === "online" ? "Ready for your next command" : mode.charAt(0).toUpperCase() + mode.slice(1);

  return (
    <section className="panel flex min-h-[520px] flex-col rounded-[28px] p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-cyanCore">Workspace</p>
          <h2 className="mt-2 text-3xl font-semibold tracking-[-0.03em] text-textPrimary">Good to go.</h2>
          <p className="mt-2 max-w-xl text-sm leading-6 text-textSecondary">
            Ask Jarvis to open apps, search the web, manage files, write code, or answer in English and Malayalam.
          </p>
        </div>
        <div className="flex items-center gap-2 rounded-2xl border border-line bg-white/[0.035] px-3 py-2 text-sm text-textSecondary">
          <CheckCircle2 size={16} className={backendOnline ? "text-emerald-400" : "text-red-400"} />
          {backendOnline ? "Systems available" : "Backend offline"}
        </div>
      </div>

      <div className="mt-8 grid flex-1 place-items-center">
        <div className="w-full max-w-2xl">
          <div className="mx-auto grid h-28 w-28 place-items-center rounded-[32px] border border-cyanCore/18 bg-cyanCore/10 shadow-accent">
            <motion.div
              className="grid h-16 w-16 place-items-center rounded-3xl bg-[#07111f] text-cyanCore"
              animate={{ scale: busy ? [1, 1.04, 1] : 1 }}
              transition={{ duration: 1.6, repeat: busy ? Infinity : 0, ease: "easeInOut" }}
            >
              {busy ? <Mic2 size={28} /> : <Bot size={28} />}
            </motion.div>
          </div>

          <div className="mt-7 text-center">
            <AnimatePresence mode="wait">
              <motion.p
                key={modeText}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
                className="text-lg font-medium text-textPrimary"
              >
                {modeText}
              </motion.p>
            </AnimatePresence>
            <p className="mt-2 text-sm text-textSecondary">Action-first assistant, not a guide screen.</p>
          </div>

          <div className="mt-7">
            <Waveform active={activeWave} />
          </div>

          <div className="mt-7 flex justify-center">
            <MicButton disabled={!backendOnline || busy} active={busy} onClick={onVoice} />
          </div>
        </div>
      </div>

      <div className="mt-8">
        <div className="mb-3 flex items-center gap-2 text-sm font-medium text-textPrimary">
          <Sparkles size={16} className="text-cyanCore" />
          Smart suggestions
        </div>
        <div className="grid gap-2 sm:grid-cols-2">
          {suggestions.map((suggestion) => (
            <button
              key={suggestion}
              type="button"
              onClick={() => onSuggestion?.(suggestion)}
              disabled={!backendOnline || busy}
              className="panel-soft min-h-11 rounded-2xl px-4 text-left text-sm text-textSecondary transition hover:border-cyanCore/20 hover:bg-cyanCore/[0.05] hover:text-textPrimary disabled:cursor-not-allowed disabled:opacity-45"
            >
              {suggestion}
            </button>
          ))}
        </div>
      </div>
    </section>
  );
}
