import { AnimatePresence, motion } from "framer-motion";

export default function ResponsePanel({ transcript, response, history }) {
  return (
    <section className="hud-panel flex min-h-[520px] flex-col p-5">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-sm font-semibold uppercase tracking-[0.28em] text-cyanSoft">Mission Feed</h2>
        <span className="h-1.5 w-16 bg-gradient-to-r from-cyanCore to-violetCore shadow-neon" />
      </div>

      <div className="mb-4 border border-cyanCore/20 bg-black/30 p-4">
        <p className="text-xs uppercase tracking-[0.24em] text-cyanSoft/60">Command</p>
        <p className="mt-2 text-lg text-white/90">{transcript}</p>
      </div>

      <div className="relative flex-1 overflow-hidden border border-cyanCore/20 bg-black/35 p-4">
        <div className="absolute right-0 top-0 h-full w-px bg-cyanCore/30" />
        <p className="text-xs uppercase tracking-[0.24em] text-cyanSoft/60">JX JARVIS</p>
        <AnimatePresence mode="wait">
          <motion.p
            key={response}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="mt-3 whitespace-pre-wrap text-xl leading-relaxed text-white"
          >
            {response}
          </motion.p>
        </AnimatePresence>
      </div>

      <div className="mt-4 max-h-44 space-y-2 overflow-auto pr-1">
        {history.map((item, index) => (
          <div key={`${item.transcript}-${index}`} className="border-l border-cyanCore/40 bg-cyanCore/[0.04] px-3 py-2">
            <p className="truncate text-xs uppercase tracking-[0.18em] text-cyanSoft/60">{item.transcript}</p>
            <p className="truncate text-sm text-white/75">{item.response}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
