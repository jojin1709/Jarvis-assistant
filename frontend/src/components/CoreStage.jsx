import { AnimatePresence, motion } from "framer-motion";
import { Bot, CheckCircle2, Mic2 } from "lucide-react";

import MicButton from "./MicButton.jsx";
import Waveform from "./Waveform.jsx";

export default function CoreStage({ mode, activeWave, backendOnline, busy, onVoice }) {
  const modeText = mode === "online" ? "Ready for your next command" : mode.charAt(0).toUpperCase() + mode.slice(1);

  return (
    <section className="panel rounded-[24px] p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-cyanCore">Workspace</p>
          <h2 className="text-2xl font-semibold tracking-[-0.03em] text-textPrimary">Good to go.</h2>
          <p className="mt-1 max-w-xl text-sm leading-5 text-textSecondary">
            Ask Jarvis to open apps, search the web, manage files, write code, or answer in English and Malayalam.
          </p>
        </div>
        <div className="flex items-center gap-2 rounded-2xl border border-line bg-white/[0.035] px-3 py-2 text-sm text-textSecondary">
          <CheckCircle2 size={16} className={backendOnline ? "text-emerald-400" : "text-red-400"} />
          {backendOnline ? "Systems available" : "Backend offline"}
        </div>
      </div>

      <div className="mt-4 grid place-items-center">
        <div className="w-full max-w-2xl">
          <div className="mx-auto grid h-[72px] w-[72px] place-items-center rounded-[22px] border border-cyanCore/18 bg-cyanCore/10 shadow-accent">
            <motion.div
              className="grid h-12 w-12 place-items-center rounded-2xl bg-[#07111f] text-cyanCore"
              animate={{ scale: busy ? [1, 1.04, 1] : 1 }}
              transition={{ duration: 1.6, repeat: busy ? Infinity : 0, ease: "easeInOut" }}
            >
              {busy ? <Mic2 size={22} /> : <Bot size={22} />}
            </motion.div>
          </div>

          <div className="mt-3 text-center">
            <AnimatePresence mode="wait">
              <motion.p
                key={modeText}
                initial={{ opacity: 0, y: 6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
                className="text-base font-medium text-textPrimary"
              >
                {modeText}
              </motion.p>
            </AnimatePresence>
            <p className="mt-1 text-sm text-textSecondary">Action-first assistant, not a guide screen.</p>
          </div>

          <div className="mt-3">
            <Waveform active={activeWave} />
          </div>

          <div className="mt-3 flex justify-center">
            <MicButton disabled={!backendOnline || busy} active={busy} onClick={onVoice} />
          </div>
        </div>
      </div>
    </section>
  );
}
