import { Loader2, Mic } from "lucide-react";
import { motion } from "framer-motion";

export default function MicButton({ disabled, active, onClick }) {
  return (
    <motion.button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className="group inline-flex h-14 items-center gap-3 rounded-2xl border border-cyanCore/20 bg-cyanCore/10 px-5 text-sm font-semibold text-cyanCore shadow-accent transition hover:bg-cyanCore/15 disabled:cursor-not-allowed disabled:opacity-50"
      whileHover={{ scale: disabled ? 1 : 1.015 }}
      whileTap={{ scale: disabled ? 1 : 0.985 }}
      title="Start listening"
    >
      <span className="grid h-8 w-8 place-items-center rounded-xl bg-cyanCore/10">
        {active ? <Loader2 className="animate-spin" size={18} /> : <Mic size={18} />}
      </span>
      {active ? "Listening" : "Speak"}
    </motion.button>
  );
}
