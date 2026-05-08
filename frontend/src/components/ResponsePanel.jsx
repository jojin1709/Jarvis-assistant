import { AnimatePresence, motion } from "framer-motion";

export default function ResponsePanel({ transcript, response, history }) {
  return (
    <section className="panel flex min-h-[520px] flex-col rounded-[28px] p-5">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-base font-semibold text-textPrimary">Mission feed</h2>
        <span className="rounded-full border border-line px-2.5 py-1 text-xs text-textSecondary">Live</span>
      </div>

      <div className="mb-4 rounded-2xl border border-line bg-white/[0.03] p-4">
        <p className="text-sm text-textSecondary">Command</p>
        <p className="mt-2 text-base text-textPrimary">{transcript}</p>
      </div>

      <div className="relative flex-1 overflow-hidden rounded-2xl border border-line bg-[#0A1020]/70 p-4">
        <p className="text-sm text-cyanCore">JX Jarvis</p>
        <AnimatePresence mode="wait">
          <motion.p
            key={response}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            className="mt-3 whitespace-pre-wrap text-lg leading-8 text-textPrimary"
          >
            {response}
          </motion.p>
        </AnimatePresence>
      </div>

      <div className="mt-4 max-h-44 space-y-2 overflow-auto pr-1">
        {history.map((item, index) => (
          <div key={`${item.transcript}-${index}`} className="rounded-2xl border border-line bg-white/[0.025] px-3 py-2">
            <p className="truncate text-xs text-textSecondary">{item.transcript}</p>
            <p className="truncate text-sm text-textPrimary/80">{item.response}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
