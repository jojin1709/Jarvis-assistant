import { AnimatePresence, motion } from "framer-motion";
import { MessageSquareText } from "lucide-react";

export default function CompactFeed({ transcript, response, history }) {
  return (
    <section className="panel rounded-[28px] p-5">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <MessageSquareText size={17} className="text-cyanCore" />
          <h2 className="text-sm font-semibold text-textPrimary">Assistant conversation</h2>
        </div>
        <span className="rounded-full border border-line px-2.5 py-1 text-xs text-textSecondary">Live</span>
      </div>

      <div className="space-y-3">
        <div className="rounded-2xl border border-line bg-white/[0.03] p-4">
          <p className="text-xs font-medium text-textSecondary">You</p>
          <p className="mt-2 line-clamp-2 text-sm leading-6 text-textPrimary">{transcript}</p>
        </div>

        <div className="min-h-36 rounded-2xl border border-line bg-[#0A1020]/70 p-4">
          <p className="text-xs font-medium text-cyanCore">Jarvis</p>
          <AnimatePresence mode="wait">
            <motion.p
              key={response}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              className="mt-2 max-h-52 overflow-auto whitespace-pre-wrap text-base leading-7 text-textPrimary"
            >
              {response}
            </motion.p>
          </AnimatePresence>
        </div>
      </div>

      {history.length > 0 && (
        <div className="mt-5">
          <p className="mb-3 text-sm font-medium text-textPrimary">Recent conversations</p>
          <div className="space-y-2">
            {history.slice(0, 3).map((item, index) => (
              <div key={`${item.transcript}-${index}`} className="rounded-2xl border border-line bg-white/[0.025] px-3 py-2.5">
                <p className="truncate text-xs text-textSecondary">{item.transcript}</p>
                <p className="mt-1 truncate text-sm text-textPrimary/80">{item.response}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
