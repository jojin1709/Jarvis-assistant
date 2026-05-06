import { motion } from "framer-motion";

export default function TopBar({ now, backendOnline }) {
  const date = now.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" });
  const time = now.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit", second: "2-digit" });

  return (
    <header className="flex flex-wrap items-center justify-between gap-4 border-b border-cyanCore/20 bg-black/25 px-5 py-4 backdrop-blur">
      <div>
        <motion.h1
          className="font-display text-2xl font-bold uppercase tracking-[0.28em] text-white drop-shadow-[0_0_18px_rgba(56,246,255,.35)] sm:text-4xl"
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          JX JARVIS
        </motion.h1>
        <p className="mt-1 text-xs uppercase tracking-[0.34em] text-cyanSoft/75">Desktop Operations Core</p>
      </div>
      <div className="text-right font-display">
        <p className="text-2xl text-cyanSoft">{time}</p>
        <p className="text-xs uppercase tracking-[0.22em] text-white/55">{date}</p>
        <p className={`mt-2 text-xs uppercase tracking-[0.22em] ${backendOnline ? "text-emerald-300" : "text-red-300"}`}>
          Backend {backendOnline ? "online" : "offline"}
        </p>
      </div>
    </header>
  );
}
