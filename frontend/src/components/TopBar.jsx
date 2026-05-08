import { motion } from "framer-motion";

export default function TopBar({ now, backendOnline }) {
  const date = now.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" });
  const time = now.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });

  return (
    <header className="app-surface flex flex-wrap items-center justify-between gap-4 rounded-[28px] px-5 py-4">
      <div>
        <motion.h1
          className="text-2xl font-semibold tracking-[-0.03em] text-textPrimary"
          initial={{ opacity: 0, y: -6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.45 }}
        >
          JX Jarvis
        </motion.h1>
        <p className="mt-1 text-sm text-textSecondary">Personal AI Workspace</p>
      </div>
      <div className="text-right">
        <p className="text-lg font-medium tabular-nums text-textPrimary">{time}</p>
        <p className="text-sm text-textSecondary">{date}</p>
        <p className={`mt-1 text-sm ${backendOnline ? "text-emerald-300" : "text-red-300"}`}>
          Backend {backendOnline ? "online" : "offline"}
        </p>
      </div>
    </header>
  );
}
