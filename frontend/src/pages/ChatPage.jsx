import { useState } from "react";
import { useOutletContext } from "react-router-dom";
import { Bot, SendHorizontal, User } from "lucide-react";

import MarkdownMessage from "../components/MarkdownMessage.jsx";

export default function ChatPage() {
  const runtime = useOutletContext();
  const [text, setText] = useState("");

  async function submit(event) {
    event.preventDefault();
    const trimmed = text.trim();
    if (!trimmed) return;
    setText("");
    await runtime.runTextFlow(trimmed);
  }

  return (
    <section className="panel flex min-h-[calc(100vh-190px)] flex-col rounded-[28px] p-5">
      <div className="mb-5">
        <h2 className="text-2xl font-semibold tracking-[-0.03em] text-textPrimary">Chat</h2>
        <p className="mt-1 text-sm text-textSecondary">Full assistant conversation with markdown and code block rendering.</p>
      </div>

      <div className="min-h-0 flex-1 space-y-4 overflow-auto pr-1">
        {runtime.chatHistory.length ? (
          runtime.chatHistory.map((item) => (
            <div key={item.id} className="space-y-3">
              <Bubble role="user" text={item.transcript} />
              <Bubble role="assistant" text={item.response} />
            </div>
          ))
        ) : (
          <div className="grid min-h-64 place-items-center rounded-[28px] border border-line bg-white/[0.025] text-center">
            <div>
              <Bot className="mx-auto mb-3 text-cyanCore" size={34} />
              <p className="font-medium text-textPrimary">Start a conversation</p>
              <p className="mt-1 text-sm text-textSecondary">Ask Jarvis to explain, write, search, open, or automate.</p>
            </div>
          </div>
        )}
      </div>

      <form className="mt-5 flex items-center gap-3 rounded-[24px] border border-line bg-white/[0.035] p-2.5" onSubmit={submit}>
        <input
          value={text}
          onChange={(event) => setText(event.target.value)}
          disabled={!runtime.backendOnline || runtime.busy}
          className="min-w-0 flex-1 bg-transparent px-3 py-3 text-textPrimary outline-none placeholder:text-textSecondary"
          placeholder="Message Jarvis..."
        />
        <button
          type="submit"
          disabled={!text.trim() || !runtime.backendOnline || runtime.busy}
          className="grid h-11 w-11 place-items-center rounded-2xl bg-cyanCore text-[#021018] disabled:opacity-40"
        >
          <SendHorizontal size={18} />
        </button>
      </form>
    </section>
  );
}

function Bubble({ role, text }) {
  const user = role === "user";
  return (
    <div className={`flex gap-3 ${user ? "justify-end" : "justify-start"}`}>
      {!user && (
        <div className="grid h-9 w-9 shrink-0 place-items-center rounded-2xl bg-cyanCore/10 text-cyanCore">
          <Bot size={17} />
        </div>
      )}
      <div className={`max-w-[78%] rounded-[24px] border border-line p-4 ${user ? "bg-cyanCore/10" : "bg-white/[0.035]"}`}>
        <MarkdownMessage>{text}</MarkdownMessage>
      </div>
      {user && (
        <div className="grid h-9 w-9 shrink-0 place-items-center rounded-2xl bg-white/[0.055] text-textSecondary">
          <User size={17} />
        </div>
      )}
    </div>
  );
}
