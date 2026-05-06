import { SendHorizontal, Terminal } from "lucide-react";
import { useState } from "react";

export default function CommandConsole({ onSend, disabled }) {
  const [text, setText] = useState("");

  function submit(event) {
    event.preventDefault();
    const trimmed = text.trim();
    if (!trimmed) return;
    onSend(trimmed);
    setText("");
  }

  return (
    <form className="hud-panel flex items-center gap-3 p-3" onSubmit={submit}>
      <Terminal className="ml-1 text-cyanSoft" size={20} />
      <input
        value={text}
        onChange={(event) => setText(event.target.value)}
        disabled={disabled}
        className="min-w-0 flex-1 bg-transparent px-2 py-3 text-lg text-white outline-none placeholder:text-cyanSoft/35"
        placeholder="Command line"
      />
      <button
        type="submit"
        disabled={disabled || !text.trim()}
        className="grid h-11 w-11 place-items-center border border-cyanCore/40 bg-cyanCore/10 text-cyanSoft transition hover:bg-cyanCore/20 disabled:opacity-40"
        title="Send command"
      >
        <SendHorizontal size={19} />
      </button>
    </form>
  );
}
