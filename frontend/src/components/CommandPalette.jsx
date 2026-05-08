import { AnimatePresence, motion } from "framer-motion";
import { Bot, Command, FileSearch, FolderPlus, Globe2, Mic2, Search, Settings, Terminal } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

const commands = [
  { label: "Open Chat", page: "/chat", icon: Bot, hint: "Go to the conversation workspace" },
  { label: "Open Voice", page: "/voice", icon: Mic2, hint: "Microphone and wake controls" },
  { label: "Open Files", page: "/files", icon: FileSearch, hint: "AI file intake and recent uploads" },
  { label: "Open Automation", page: "/automation", icon: Terminal, hint: "Plans, logs, and routines" },
  { label: "Open Browser", page: "/browser", icon: Globe2, hint: "Visual browser operator" },
  { label: "Open Settings", page: "/settings", icon: Settings, hint: "Providers, voice, startup" },
  { label: "Open Downloads", text: "open downloads", icon: FolderPlus, hint: "Desktop action" },
  { label: "Search Google Visually", text: "search google for ", icon: Search, hint: "Open browser, type, and show results live" },
  { label: "Search YouTube Visually", text: "open youtube and search ", icon: Globe2, hint: "Open YouTube and type the search live" },
  { label: "Open VS Code", text: "open vs code", icon: Terminal, hint: "Launch a desktop app" },
  { label: "Run Autonomous Task", agent: true, text: "", icon: Command, hint: "Plan and execute with tools" },
];

export default function CommandPalette({ open, onClose, onRun }) {
  const [query, setQuery] = useState("");
  const navigate = useNavigate();
  const filtered = useMemo(() => {
    const normalized = query.toLowerCase().trim();
    if (!normalized) return commands;
    return commands.filter((command) => `${command.label} ${command.hint}`.toLowerCase().includes(normalized));
  }, [query]);

  useEffect(() => {
    if (open) setQuery("");
  }, [open]);

  function run(command) {
    if (command.page) {
      navigate(command.page);
      onClose();
      return;
    }

    const text = command.text || query;
    if (!text.trim()) return;
    onRun(text, { agent: command.agent });
    onClose();
  }

  function submit(event) {
    event.preventDefault();
    const first = filtered[0];
    if (first && !query.trim()) run(first);
    else if (first?.text?.endsWith(" ")) run({ ...first, text: `${first.text}${query}` });
    else onRun(query, { agent: true });
    onClose();
  }

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-50 grid place-items-start bg-black/45 px-4 pt-[12vh] backdrop-blur-sm"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onMouseDown={onClose}
        >
          <motion.form
            className="app-surface mx-auto w-full max-w-2xl overflow-hidden rounded-[28px]"
            initial={{ opacity: 0, y: 18, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 12, scale: 0.98 }}
            onMouseDown={(event) => event.stopPropagation()}
            onSubmit={submit}
          >
            <div className="flex items-center gap-3 border-b border-line p-4">
              <Command size={20} className="text-cyanCore" />
              <input
                autoFocus
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                className="min-w-0 flex-1 bg-transparent text-lg text-textPrimary outline-none placeholder:text-textSecondary"
                placeholder="Search commands or describe a task..."
              />
              <span className="rounded-lg border border-line px-2 py-1 text-xs text-textSecondary">Ctrl K</span>
            </div>

            <div className="max-h-[420px] overflow-auto p-2">
              {filtered.map((command) => {
                const Icon = command.icon;
                return (
                  <button
                    key={command.label}
                    type="button"
                    onClick={() => run(command)}
                    className="flex w-full items-center gap-3 rounded-2xl px-3 py-3 text-left transition hover:bg-white/[0.055]"
                  >
                    <span className="grid h-10 w-10 place-items-center rounded-2xl bg-white/[0.045] text-cyanCore">
                      <Icon size={18} />
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="block text-sm font-medium text-textPrimary">{command.label}</span>
                      <span className="block truncate text-sm text-textSecondary">{command.hint}</span>
                    </span>
                  </button>
                );
              })}
            </div>
          </motion.form>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
