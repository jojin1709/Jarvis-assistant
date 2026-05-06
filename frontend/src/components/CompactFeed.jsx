import { AnimatePresence, motion } from "framer-motion";

export default function CompactFeed({ transcript, response, history }) {
  return (
    <section className="hud-panel rounded-2xl p-4">
      <div className="mb-3 flex items-center justify-between">
        <p className="text-xs uppercase tracking-[0.24em] text-cyanSoft">Jarvis Feed</p>
        <span className="h-px w-24 bg-cyanCore/40" />
      </div>

      <div className="rounded-xl border border-cyanCore/15 bg-black/30 p-3">
        <p className="text-[11px] uppercase tracking-[0.2em] text-cyanSoft/50">You</p>
        <p className="mt-1 line-clamp-2 text-base text-white/80">{transcript}</p>
      </div>

      <div className="mt-3 min-h-32 rounded-xl border border-cyanCore/20 bg-black/35 p-4">
        <p className="text-[11px] uppercase tracking-[0.2em] text-cyanSoft/50">JX JARVIS</p>
        <AnimatePresence mode="wait">
          <motion.p
            key={response}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            className="mt-2 max-h-36 overflow-auto whitespace-pre-wrap text-lg leading-relaxed text-white"
          >
            {response}
          </motion.p>
        </AnimatePresence>
      </div>

      {history.length > 0 && (
        <div className="mt-3 grid gap-2 sm:grid-cols-2">
          {history.slice(0, 2).map((item, index) => (
            <div key={`${item.transcript}-${index}`} className="rounded-lg border border-cyanCore/10 bg-cyanCore/[0.035] px-3 py-2">
              <p className="truncate text-[11px] uppercase tracking-[0.16em] text-cyanSoft/45">{item.transcript}</p>
              <p className="truncate text-sm text-white/60">{item.response}</p>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
