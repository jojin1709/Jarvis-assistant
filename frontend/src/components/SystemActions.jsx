import {
  Calculator,
  CalendarDays,
  Camera,
  Chrome,
  Clock,
  Code2,
  FileText,
  FolderOpen,
  Github,
  Mail,
  MessageCircle,
  MonitorCog,
  Music,
  NotebookPen,
  Search,
  Youtube,
} from "lucide-react";

const actions = [
  { id: "open_notepad", label: "Notepad", icon: NotebookPen },
  { id: "open_calculator", label: "Calculator", icon: Calculator },
  { id: "open_explorer", label: "Files", icon: FolderOpen },
  { id: "open_vscode", label: "Code", icon: Code2 },
  { id: "list_desktop", label: "Desktop", icon: Search },
  { id: "system_status", label: "Status", icon: MonitorCog },
  { id: "create_note", label: "Note", icon: FileText },
  { id: "open_youtube", label: "YouTube", icon: Youtube },
  { id: "open_google", label: "Google", icon: Search },
  { id: "open_chrome", label: "Chrome", icon: Chrome },
  { id: "open_gmail", label: "Gmail", icon: Mail },
  { id: "open_github", label: "GitHub", icon: Github },
  { id: "open_whatsapp", label: "WhatsApp", icon: MessageCircle },
  { id: "take_screenshot", label: "Screenshot", icon: Camera },
  { id: "play_music", label: "Music", icon: Music },
  { id: "current_time", label: "Time", icon: Clock },
  { id: "current_date", label: "Date", icon: CalendarDays },
];

export default function SystemActions({ disabled, onRun }) {
  return (
    <section className="panel rounded-[28px] p-5">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-textPrimary">AI actions</h2>
          <p className="mt-1 text-sm text-textSecondary">Safe local shortcuts</p>
        </div>
        <span className="rounded-full border border-emerald-400/20 bg-emerald-400/10 px-2.5 py-1 text-xs text-emerald-300">Ready</span>
      </div>

      <div className="grid grid-cols-2 gap-2">
        {actions.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            type="button"
            disabled={disabled}
            onClick={() => onRun(id)}
            title={label}
            className="panel-soft flex h-12 items-center justify-center gap-2 rounded-2xl text-sm font-medium text-textSecondary transition hover:bg-white/[0.055] hover:text-textPrimary disabled:cursor-not-allowed disabled:opacity-40"
          >
            <Icon size={16} />
            {label}
          </button>
        ))}
      </div>
    </section>
  );
}
