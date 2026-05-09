import { motion } from "framer-motion";

const bars = Array.from({ length: 28 }, (_, index) => index);

export default function Waveform({ active }) {
  return (
    <div className="flex h-12 items-center justify-center gap-1.5 rounded-2xl border border-line bg-white/[0.025] px-5">
      {bars.map((bar) => (
        <motion.span
          key={bar}
          className="block w-1 rounded-full bg-cyanCore/75"
          animate={{
            height: active ? [8, 18 + ((bar * 7) % 26), 10 + ((bar * 5) % 18)] : [6, 9, 6],
            opacity: active ? [0.35, 0.95, 0.5] : [0.22, 0.38, 0.22],
          }}
          transition={{ duration: 0.9 + (bar % 5) * 0.08, repeat: Infinity, ease: "easeInOut" }}
        />
      ))}
    </div>
  );
}
