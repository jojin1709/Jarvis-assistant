import { Maximize2, Minus, Square, X } from "lucide-react";
import { useEffect, useState } from "react";

export default function WindowTitleBar() {
  const [maximized, setMaximized] = useState(false);
  const desktop = window.jxJarvis;

  useEffect(() => {
    let cleanup;
    desktop?.isMaximized?.().then(setMaximized).catch(() => {});
    if (desktop?.onWindowState) {
      cleanup = desktop.onWindowState((state) => setMaximized(Boolean(state.maximized)));
    }
    return () => cleanup?.();
  }, [desktop]);

  return (
    <div className="window-drag flex h-11 shrink-0 items-center justify-between border-b border-cyanCore/20 bg-black/55 pl-4 backdrop-blur-xl">
      <div className="flex items-center gap-3">
        <div className="grid h-6 w-6 place-items-center border border-cyanCore/40 bg-cyanCore/10 text-[10px] font-bold text-cyanSoft shadow-neon">
          JX
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-white/85">JX JARVIS</p>
          <p className="text-[10px] uppercase tracking-[0.2em] text-cyanSoft/55">Standalone Desktop Core</p>
        </div>
      </div>

      <div className="window-no-drag flex h-full">
        <button
          type="button"
          onClick={() => desktop?.minimize?.()}
          className="grid h-11 w-12 place-items-center text-cyanSoft/80 transition hover:bg-cyanCore/10 hover:text-white"
          title="Minimize"
        >
          <Minus size={16} />
        </button>
        <button
          type="button"
          onClick={() => desktop?.maximize?.()}
          className="grid h-11 w-12 place-items-center text-cyanSoft/80 transition hover:bg-cyanCore/10 hover:text-white"
          title={maximized ? "Restore" : "Maximize"}
        >
          {maximized ? <Square size={14} /> : <Maximize2 size={15} />}
        </button>
        <button
          type="button"
          onClick={() => desktop?.close?.()}
          className="grid h-11 w-12 place-items-center text-cyanSoft/80 transition hover:bg-red-500/75 hover:text-white"
          title="Close"
        >
          <X size={17} />
        </button>
      </div>
    </div>
  );
}
