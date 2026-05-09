import { Command, SendHorizontal } from "lucide-react";
import { useState } from "react";

export default function CommandConsole({ onSend, disabled }) {
  const [text, setText] = useState("");

  function submit(event) {
    event.preventDefault();
    const trimmed = text.trim();
    if (!trimmed) return;
    Promise.resolve(onSend(trimmed)).catch(() => {});
    setText("");
  }

  return (
    <form className="app-surface flex items-center gap-2 rounded-[20px] p-2" onSubmit={submit}>
      <div className="grid h-9 w-9 place-items-center rounded-2xl bg-white/[0.045] text-textSecondary">
        <Command size={17} />
      </div>
      <input
        value={text}
        onChange={(event) => setText(event.target.value)}
        disabled={disabled}
        className="min-w-0 flex-1 bg-transparent px-1 py-2 text-sm text-textPrimary outline-none placeholder:text-textSecondary/65"
        placeholder="Ask Jarvis to open apps, search, write, remember, or manage files..."
      />
      <button
        type="submit"
        disabled={disabled || !text.trim()}
        className="grid h-10 w-10 place-items-center rounded-2xl bg-cyanCore text-[#021018] transition hover:bg-cyanSoft disabled:cursor-not-allowed disabled:opacity-40"
        title="Send command"
      >
        <SendHorizontal size={18} />
      </button>
    </form>
  );
}
