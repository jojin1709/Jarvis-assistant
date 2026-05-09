import { Camera, Command, Mic2, Send, X } from "lucide-react";
import { useState } from "react";

export default function AssistantOverlay({ open, onClose, runtime }) {
  const [text, setText] = useState("");
  if (!open) return null;

  async function submit(event) {
    event?.preventDefault();
    if (!text.trim()) return;
    const command = text.trim();
    setText("");
    try {
      await runtime.runTextFlow(command, { agent: true });
    } catch (error) {
      runtime.addExecutionLog({ message: error?.message || "Overlay command failed", level: "error" });
    }
  }

  return (
    <div className="fixed inset-0 z-50 grid place-items-start bg-black/35 px-4 pt-[14vh] backdrop-blur-md">
      <div className="mx-auto w-full max-w-2xl overflow-hidden rounded-[26px] border border-white/10 bg-[#0B1220]/95 shadow-2xl shadow-cyanCore/10">
        <div className="flex items-center justify-between border-b border-line px-4 py-3">
          <div className="flex items-center gap-2 text-sm font-medium text-textPrimary">
            <Command size={16} className="text-cyanCore" />
            Jarvis overlay
          </div>
          <button type="button" onClick={onClose} className="grid h-8 w-8 place-items-center rounded-xl text-textSecondary hover:bg-white/[0.06]">
            <X size={16} />
          </button>
        </div>

        <form onSubmit={submit} className="p-4">
          <textarea
            value={text}
            onChange={(event) => setText(event.target.value)}
            autoFocus
            className="min-h-28 w-full resize-none rounded-2xl border border-line bg-[#070B14]/80 p-4 text-lg text-textPrimary outline-none placeholder:text-textSecondary"
            placeholder="Ask Jarvis to open apps, control browser, generate code, analyze screen..."
          />
          <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
            <div className="flex gap-2">
              <button
                type="button"
                onClick={runtime.runVoiceFlow}
                disabled={!runtime.backendOnline || runtime.busy}
                className="inline-flex h-10 items-center gap-2 rounded-xl border border-line bg-white/[0.035] px-3 text-sm text-textSecondary hover:text-textPrimary disabled:cursor-not-allowed disabled:opacity-40"
              >
                <Mic2 size={15} />
                Voice
              </button>
              <button
                type="button"
                onClick={runtime.captureVisionFlow}
                disabled={!runtime.backendOnline || runtime.busy}
                className="inline-flex h-10 items-center gap-2 rounded-xl border border-line bg-white/[0.035] px-3 text-sm text-textSecondary hover:text-textPrimary disabled:cursor-not-allowed disabled:opacity-40"
              >
                <Camera size={15} />
                Screen
              </button>
            </div>
            <button
              type="submit"
              disabled={!text.trim() || !runtime.backendOnline || runtime.busy}
              className="inline-flex h-10 items-center gap-2 rounded-xl bg-cyanCore px-4 text-sm font-semibold text-[#021018] disabled:opacity-40"
            >
              <Send size={15} />
              Execute
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
