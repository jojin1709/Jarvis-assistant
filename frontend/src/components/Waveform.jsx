import { motion } from "framer-motion";

const bars = Array.from({ length: 34 }, (_, index) => index);

export default function Waveform({ active }) {
  return (
    <div className="flex h-20 items-center justify-center gap-1 overflow-hidden border-y border-cyanCore/20 bg-cyanCore/[0.025] px-4">
      {bars.map((bar) => (
        <motion.span
          key={bar}
          className="block w-1 rounded bg-cyanCore shadow-[0_0_12px_rgba(56,246,255,.65)]"
          animate={{
            height: active ? [10, 20 + ((bar * 7) % 42), 12 + ((bar * 5) % 28)] : [8, 12, 8],
            opacity: active ? [0.35, 1, 0.5] : [0.22, 0.4, 0.22],
          }}
          transition={{ duration: 0.75 + (bar % 5) * 0.08, repeat: Infinity, ease: "easeInOut" }}
        />
      ))}
    </div>
  );
}
