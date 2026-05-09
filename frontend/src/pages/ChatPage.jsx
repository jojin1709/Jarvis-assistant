import { useState } from "react";
import { useOutletContext } from "react-router-dom";
import { Bot, Clock3, SendHorizontal, Trash2, User } from "lucide-react";

import MarkdownMessage from "../components/MarkdownMessage.jsx";

export default function ChatPage() {
  const runtime = useOutletContext();
  const [text, setText] = useState("");

  async function submit(event) {
    event.preventDefault();
    const trimmed = text.trim();
    if (!trimmed) return;
    setText("");
    try {
      await runtime.runTextFlow(trimmed);
    } catch {
      // Runtime already records the error in the response panel and logs.
    }
  }

  function clearChat() {
    if (!runtime.chatHistory.length) return;
    runtime.clearChatHistory();
    runtime.addExecutionLog({ message: "Chat history cleared", level: "warning" });
  }

  return (
    <section className="panel flex h-full min-h-0 flex-col rounded-[24px] p-4">
      <div className="mb-3 shrink-0 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold tracking-[-0.03em] text-textPrimary">Chat</h2>
          <p className="mt-1 text-sm text-textSecondary">Full assistant conversation with markdown and code block rendering.</p>
        </div>
        <button
          type="button"
          disabled={!runtime.chatHistory.length}
          onClick={clearChat}
          className="inline-flex h-10 items-center gap-2 rounded-2xl border border-line bg-white/[0.035] px-3 text-sm font-medium text-textSecondary transition hover:border-red-400/30 hover:bg-red-400/10 hover:text-red-200 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <Trash2 size={15} />
          Clear chat
        </button>
      </div>

      <div className="min-h-0 flex-1 space-y-3 overflow-auto pr-1">
        {runtime.chatHistory.length ? (
          runtime.chatHistory.map((item) => (
            <div key={item.id} className="space-y-3">
              <ConversationTime createdAt={item.createdAt} />
              <Bubble role="user" text={item.transcript} />
              <Bubble role="assistant" text={item.response} />
            </div>
          ))
        ) : (
          <div className="grid min-h-full place-items-center rounded-[24px] border border-line bg-white/[0.025] text-center">
            <div>
              <Bot className="mx-auto mb-3 text-cyanCore" size={34} />
              <p className="font-medium text-textPrimary">Start a conversation</p>
              <p className="mt-1 text-sm text-textSecondary">Ask Jarvis to explain, write, search, open, or automate.</p>
            </div>
          </div>
        )}
      </div>

      <form className="mt-3 flex items-center gap-2 rounded-[20px] border border-line bg-white/[0.035] p-2" onSubmit={submit}>
        <input
          value={text}
          onChange={(event) => setText(event.target.value)}
          disabled={!runtime.backendOnline || runtime.busy}
          className="min-w-0 flex-1 bg-transparent px-3 py-2 text-sm text-textPrimary outline-none placeholder:text-textSecondary"
          placeholder="Message Jarvis..."
        />
        <button
          type="submit"
          disabled={!text.trim() || !runtime.backendOnline || runtime.busy}
          className="grid h-10 w-10 place-items-center rounded-2xl bg-cyanCore text-[#021018] disabled:opacity-40"
        >
          <SendHorizontal size={18} />
        </button>
      </form>
    </section>
  );
}

function ConversationTime({ createdAt }) {
  const stamp = formatTimestamp(createdAt);
  return (
    <div className="flex justify-center">
      <span className="inline-flex items-center gap-2 rounded-full border border-line bg-white/[0.035] px-3 py-1 text-xs text-textSecondary">
        <Clock3 size={13} className="text-cyanCore" />
        {stamp}
      </span>
    </div>
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
      <div className={`max-w-[78%] rounded-[22px] border border-line p-3 ${user ? "bg-cyanCore/10" : "bg-white/[0.035]"}`}>
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

function formatTimestamp(value) {
  const date = value ? new Date(value) : new Date();
  if (Number.isNaN(date.getTime())) return "Time unavailable";
  return date.toLocaleString([], {
    weekday: "short",
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
