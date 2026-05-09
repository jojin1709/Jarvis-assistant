import { Loader2, Mic } from "lucide-react";
import { motion } from "framer-motion";

export default function MicButton({ disabled, active, onClick }) {
  return (
    <motion.button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className="group inline-flex h-11 items-center gap-2 rounded-2xl border border-cyanCore/20 bg-cyanCore/10 px-4 text-sm font-semibold text-cyanCore shadow-accent transition hover:bg-cyanCore/15 disabled:cursor-not-allowed disabled:opacity-50"
      whileHover={{ scale: disabled ? 1 : 1.015 }}
      whileTap={{ scale: disabled ? 1 : 0.985 }}
      title="Start listening"
    >
      <span className="grid h-7 w-7 place-items-center rounded-xl bg-cyanCore/10">
        {active ? <Loader2 className="animate-spin" size={16} /> : <Mic size={16} />}
      </span>
      {active ? "Listening" : "Speak"}
    </motion.button>
  );
}
