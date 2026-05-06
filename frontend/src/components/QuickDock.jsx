import { Calculator, Clock, FileUp, FolderOpen, Music, NotebookPen, Radio, Search, Youtube } from "lucide-react";

const actions = [
  { type: "task", id: "open_youtube", label: "YouTube", icon: Youtube },
  { type: "task", id: "open_explorer", label: "Files", icon: FolderOpen },
  { type: "task", id: "open_calculator", label: "Calc", icon: Calculator },
  { type: "task", id: "play_music", label: "Music", icon: Music },
  { type: "task", id: "current_time", label: "Time", icon: Clock },
  { type: "task", id: "create_note", label: "Note", icon: NotebookPen },
];

export default function QuickDock({ disabled, wakeEnabled, onRun, onToggleWake, onUploadClick }) {
  return (
    <div className="grid grid-cols-4 gap-2 sm:grid-cols-8">
      <button
        type="button"
        disabled={disabled}
        onClick={onToggleWake}
        className={`quick-action ${wakeEnabled ? "active" : ""}`}
        title={wakeEnabled ? "Wake word is armed" : "Wake word is off"}
      >
        <Radio size={18} />
        <span>Wake</span>
      </button>
      <button
        type="button"
        disabled={disabled}
        onClick={onUploadClick}
        className="quick-action"
        title="Upload file"
      >
        <FileUp size={18} />
        <span>Upload</span>
      </button>
      {actions.map(({ id, label, icon: Icon }) => (
        <button key={id} type="button" disabled={disabled} onClick={() => onRun(id)} className="quick-action" title={label}>
          <Icon size={18} />
          <span>{label}</span>
        </button>
      ))}
      <button
        type="button"
        disabled={disabled}
        onClick={() => onRun("list_desktop")}
        className="quick-action sm:hidden"
        title="Scan desktop"
      >
        <Search size={18} />
        <span>Scan</span>
      </button>
    </div>
  );
}
