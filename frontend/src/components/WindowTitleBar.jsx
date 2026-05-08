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
    <div className="window-drag flex h-11 shrink-0 items-center justify-between border-b border-line bg-[#070B14]/70 pl-4 backdrop-blur-2xl">
      <div className="flex items-center gap-3">
        <div className="grid h-6 w-6 place-items-center rounded-lg border border-white/10 bg-white/[0.04] text-[11px] font-semibold text-cyanCore">
          JX
        </div>
        <div className="flex items-baseline gap-2">
          <p className="text-sm font-semibold text-textPrimary">JX Jarvis</p>
          <p className="text-xs text-textSecondary">Personal AI Workspace</p>
        </div>
      </div>

      <div className="window-no-drag flex h-full">
        <button
          type="button"
          onClick={() => desktop?.minimize?.()}
          className="grid h-11 w-12 place-items-center rounded-none text-textSecondary transition hover:bg-white/[0.06] hover:text-textPrimary"
          title="Minimize"
        >
          <Minus size={16} />
        </button>
        <button
          type="button"
          onClick={() => desktop?.maximize?.()}
          className="grid h-11 w-12 place-items-center rounded-none text-textSecondary transition hover:bg-white/[0.06] hover:text-textPrimary"
          title={maximized ? "Restore" : "Maximize"}
        >
          {maximized ? <Square size={14} /> : <Maximize2 size={15} />}
        </button>
        <button
          type="button"
          onClick={() => desktop?.close?.()}
          className="grid h-11 w-12 place-items-center rounded-none text-textSecondary transition hover:bg-red-500/80 hover:text-white"
          title="Close"
        >
          <X size={17} />
        </button>
      </div>
    </div>
  );
}
