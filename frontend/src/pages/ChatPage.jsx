import { useState } from "react";
import { useOutletContext } from "react-router-dom";
import { Bot, Clock3, Download, Plus, Search, SendHorizontal, Trash2, User } from "lucide-react";

import MarkdownMessage from "../components/MarkdownMessage.jsx";
import { API_BASE } from "../services/api.js";

const MESSAGES_PER_PAGE = 50;

export default function ChatPage() {
  const runtime = useOutletContext();
  const [text, setText] = useState("");
  const [googleMode, setGoogleMode] = useState(false);
  const [page, setPage] = useState(1);

  async function submit(event) {
    event.preventDefault();
    const trimmed = text.trim();
    if (!trimmed) return;
    setText("");
    try {
      await runtime.runTextFlow(trimmed, { google: googleMode });
    } catch {
      // Runtime already records the error in the response panel and logs.
    }
  }

  function clearChat() {
    if (!runtime.chatHistory.length) return;
    runtime.clearChatHistory();
    runtime.addExecutionLog({ message: "Current chat cleared", level: "warning" });
  }

  function newChat() {
    runtime.startNewChat();
    setPage(1);
    runtime.addExecutionLog({ message: "Started a new chat thread", level: "info" });
  }

  async function exportChat() {
    const response = await fetch(`${API_BASE}/api/memory/export`);
    if (!response.ok) {
      runtime.addExecutionLog({ message: "Chat export failed", level: "error" });
      return;
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `jarvis-chat-${new Date().toISOString().split("T")[0]}.json`;
    anchor.click();
    URL.revokeObjectURL(url);
    runtime.addExecutionLog({ message: "Chat memory exported", level: "success" });
  }

  const visibleHistory = runtime.chatHistory.slice(0, MESSAGES_PER_PAGE * page);
  const hasMore = runtime.chatHistory.length > visibleHistory.length;

  return (
    <section className="panel flex h-full min-h-0 flex-col rounded-[24px] p-4">
      <div className="mb-3 shrink-0 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold tracking-[-0.03em] text-textPrimary">Chat</h2>
          <p className="mt-1 text-sm text-textSecondary">Active thread context is kept for follow-up replies.</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            disabled={runtime.busy}
            onClick={newChat}
            className="inline-flex h-10 items-center gap-2 rounded-2xl border border-cyanCore/25 bg-cyanCore/10 px-3 text-sm font-medium text-cyanCore transition hover:border-cyanCore/50 hover:bg-cyanCore/15 disabled:cursor-not-allowed disabled:opacity-40"
          >
            <Plus size={16} />
            New chat
          </button>
          <button
            type="button"
            disabled={runtime.busy}
            onClick={exportChat}
            className="inline-flex h-10 items-center gap-2 rounded-2xl border border-line bg-white/[0.035] px-3 text-sm font-medium text-textSecondary transition hover:border-white/20 hover:text-textPrimary disabled:cursor-not-allowed disabled:opacity-40"
          >
            <Download size={15} />
            Export
          </button>
          <button
            type="button"
            disabled={!runtime.chatHistory.length || runtime.busy}
            onClick={clearChat}
            className="inline-flex h-10 items-center gap-2 rounded-2xl border border-line bg-white/[0.035] px-3 text-sm font-medium text-textSecondary transition hover:border-red-400/30 hover:bg-red-400/10 hover:text-red-200 disabled:cursor-not-allowed disabled:opacity-40"
          >
            <Trash2 size={15} />
            Clear current
          </button>
        </div>
      </div>

      {runtime.chatThreads?.length > 1 && (
        <div className="mb-3 flex shrink-0 gap-2 overflow-x-auto pb-1">
          {runtime.chatThreads.map((thread) => {
            const active = thread.id === runtime.activeChatId;
            return (
              <button
                key={thread.id}
                type="button"
                disabled={runtime.busy}
                onClick={() => runtime.selectChatThread(thread.id)}
                className={`max-w-[220px] shrink-0 truncate rounded-2xl border px-3 py-2 text-left text-xs font-medium transition disabled:cursor-not-allowed disabled:opacity-50 ${
                  active
                    ? "border-cyanCore/40 bg-cyanCore/10 text-cyanCore"
                    : "border-line bg-white/[0.025] text-textSecondary hover:border-white/20 hover:text-textPrimary"
                }`}
                title={thread.title || "New chat"}
              >
                {thread.title || "New chat"}
              </button>
            );
          })}
        </div>
      )}

      <div className="min-h-0 flex-1 space-y-3 overflow-auto pr-1">
        {runtime.chatHistory.length ? (
          <>
            {hasMore && (
              <button
                type="button"
                onClick={() => setPage((current) => current + 1)}
                className="w-full rounded-2xl border border-line py-2 text-sm text-textSecondary transition hover:text-textPrimary"
              >
                Load older messages ({runtime.chatHistory.length - visibleHistory.length} more)
              </button>
            )}
            {[...visibleHistory].reverse().map((item) => (
              <div key={item.id} className="space-y-3">
                <ConversationTime createdAt={item.createdAt} />
                <Bubble role="user" text={item.transcript} />
                <Bubble role="assistant" text={item.response} />
              </div>
            ))}
          </>
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
          placeholder={googleMode ? "Search Google in Chrome..." : "Message Jarvis..."}
        />
        <button
          type="button"
          disabled={!runtime.backendOnline || runtime.busy}
          onClick={() => setGoogleMode((active) => !active)}
          className={`inline-flex h-10 shrink-0 items-center gap-1 rounded-2xl border px-3 text-xs font-semibold transition disabled:cursor-not-allowed disabled:opacity-40 ${
            googleMode
              ? "border-cyanCore/50 bg-cyanCore/15 text-cyanCore"
              : "border-line bg-white/[0.035] text-textSecondary hover:border-white/20 hover:text-textPrimary"
          }`}
          title="Toggle Google search mode"
          aria-pressed={googleMode}
        >
          <Search size={14} />
          GG
        </button>
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
