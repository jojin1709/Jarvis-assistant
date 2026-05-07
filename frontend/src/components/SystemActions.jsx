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
  { id: "open_calculator", label: "Calc", icon: Calculator },
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
  { id: "take_screenshot", label: "Shot", icon: Camera },
  { id: "play_music", label: "Music", icon: Music },
  { id: "current_time", label: "Time", icon: Clock },
  { id: "current_date", label: "Date", icon: CalendarDays },
];

export default function SystemActions({ disabled, onRun }) {
  return (
    <section className="hud-panel p-4">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.28em] text-cyanSoft">Operator</p>
          <p className="mt-1 text-sm text-white/55">Safe local actions</p>
        </div>
        <span className="border border-emerald-300/30 bg-emerald-300/10 px-2 py-1 text-[10px] uppercase tracking-[0.18em] text-emerald-200">
          Armed
        </span>
      </div>

      <div className="grid grid-cols-2 gap-2">
        {actions.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            type="button"
            disabled={disabled}
            onClick={() => onRun(id)}
            title={label}
            className="flex h-14 items-center justify-center gap-2 border border-cyanCore/25 bg-black/25 text-sm uppercase tracking-[0.16em] text-cyanSoft transition hover:border-cyanSoft hover:bg-cyanCore/15 disabled:opacity-40"
          >
            <Icon size={17} />
            {label}
          </button>
        ))}
      </div>
    </section>
  );
}
