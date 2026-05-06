import { motion } from "framer-motion";

const rings = [1, 1.18, 1.36];

export default function Orb({ mode }) {
  const active = ["listening", "thinking", "speaking"].includes(mode);

  return (
    <div className="relative grid aspect-square w-full max-w-[430px] place-items-center">
      {rings.map((scale, index) => (
        <motion.div
          key={scale}
          className="absolute h-[64%] w-[64%] rounded-full border border-cyanCore/30"
          animate={{
            scale: active ? [scale, scale + 0.05, scale] : [scale, scale + 0.015, scale],
            rotate: index % 2 === 0 ? 360 : -360,
            opacity: active ? [0.35, 0.85, 0.35] : [0.2, 0.45, 0.2],
          }}
          transition={{ duration: 4.4 + index, repeat: Infinity, ease: "linear" }}
          style={{ boxShadow: "0 0 28px rgba(56,246,255,.24), inset 0 0 24px rgba(168,85,247,.12)" }}
        />
      ))}

      <motion.div
        className="absolute h-[46%] w-[46%] rounded-full border border-violetCore/40"
        animate={{ rotate: -360 }}
        transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
      />

      <motion.div
        className="relative h-[38%] w-[38%] rounded-full border border-cyanSoft/80 bg-cyanCore/10"
        animate={{
          scale: active ? [1, 1.08, 1] : [1, 1.025, 1],
          boxShadow: active
            ? [
                "0 0 28px rgba(56,246,255,.55), inset 0 0 30px rgba(56,246,255,.25)",
                "0 0 70px rgba(56,246,255,.9), inset 0 0 40px rgba(168,85,247,.28)",
                "0 0 28px rgba(56,246,255,.55), inset 0 0 30px rgba(56,246,255,.25)",
              ]
            : "0 0 32px rgba(56,246,255,.42), inset 0 0 24px rgba(56,246,255,.22)",
        }}
        transition={{ duration: 1.6, repeat: Infinity, ease: "easeInOut" }}
      >
        <div className="absolute inset-[18%] rounded-full bg-cyanSoft/35 blur-md" />
        <div className="absolute inset-[34%] rounded-full bg-white/80 shadow-neon" />
      </motion.div>
    </div>
  );
}
