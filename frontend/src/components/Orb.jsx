import { motion } from "framer-motion";
import { Bot } from "lucide-react";

export default function Orb({ mode }) {
  const active = ["listening", "thinking", "speaking"].includes(mode);

  return (
    <div className="relative grid aspect-square w-full max-w-[240px] place-items-center">
      <motion.div
        className="absolute inset-10 rounded-[42px] border border-cyanCore/15 bg-cyanCore/5"
        animate={{ scale: active ? [1, 1.04, 1] : [1, 1.015, 1] }}
        transition={{ duration: 2.4, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="grid h-24 w-24 place-items-center rounded-[32px] border border-line bg-white/[0.04] text-cyanCore shadow-accent"
        animate={{ y: active ? [0, -3, 0] : 0 }}
        transition={{ duration: 1.8, repeat: active ? Infinity : 0, ease: "easeInOut" }}
      >
        <Bot size={34} />
      </motion.div>
    </div>
  );
}
