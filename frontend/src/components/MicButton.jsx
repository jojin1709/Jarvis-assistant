import { Mic, Loader2 } from "lucide-react";
import { motion } from "framer-motion";

export default function MicButton({ disabled, active, onClick }) {
  return (
    <motion.button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className="group relative grid h-24 w-24 place-items-center rounded-full border border-cyanCore/70 bg-cyanCore/10 font-display text-cyanSoft shadow-[0_0_44px_rgba(56,246,255,.36)] transition hover:bg-cyanCore/20 disabled:cursor-not-allowed disabled:opacity-55"
      whileHover={{ scale: disabled ? 1 : 1.03 }}
      whileTap={{ scale: disabled ? 1 : 0.98 }}
      title="Activate microphone"
    >
      <span className="absolute inset-[-9px] rounded-full border border-cyanCore/25" />
      <span className="absolute inset-0 rounded-full opacity-0 shadow-[inset_0_0_32px_rgba(56,246,255,.28)] transition group-hover:opacity-100" />
      {active ? <Loader2 className="animate-spin" size={30} /> : <Mic size={32} />}
      <span className="absolute -bottom-8 text-xs font-semibold uppercase tracking-[0.22em]">{active ? "Active" : "Speak"}</span>
    </motion.button>
  );
}
