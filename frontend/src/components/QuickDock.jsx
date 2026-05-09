import { Calculator, Clock, Code2, FileUp, FolderOpen, Music, Radio, Search, Youtube } from "lucide-react";

const actions = [
  { type: "task", id: "open_youtube", label: "YouTube", icon: Youtube },
  { type: "task", id: "open_explorer", label: "Files", icon: FolderOpen },
  { type: "task", id: "open_vscode", label: "Code", icon: Code2 },
  { type: "task", id: "open_calculator", label: "Calculator", icon: Calculator },
  { type: "task", id: "play_music", label: "Music", icon: Music },
  { type: "task", id: "current_time", label: "Time", icon: Clock },
];

export default function QuickDock({ disabled, wakeEnabled, onRun, onToggleWake, onUploadClick }) {
  return (
    <div className="grid gap-2 sm:grid-cols-3 xl:grid-cols-5">
      <QuickButton
        disabled={disabled}
        active={wakeEnabled}
        onClick={onToggleWake}
        icon={Radio}
        label={wakeEnabled ? "Wake active" : "Wake off"}
        title={wakeEnabled ? "Wake word is armed" : "Wake word is off"}
      />
      <QuickButton disabled={disabled} onClick={onUploadClick} icon={FileUp} label="Upload file" title="Upload file" />
      {actions.map(({ id, label, icon }) => (
        <QuickButton key={id} disabled={disabled} onClick={() => onRun(id)} icon={icon} label={label} title={label} />
      ))}
      <QuickButton disabled={disabled} onClick={() => onRun("list_desktop")} icon={Search} label="Scan desktop" title="Scan desktop" />
    </div>
  );
}

function QuickButton({ disabled, active, onClick, icon: Icon, label, title }) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={`panel-soft flex min-h-10 items-center gap-2 rounded-2xl px-3 text-left transition ${
        active ? "border-cyanCore/25 bg-cyanCore/[0.07] text-cyanCore" : "text-textSecondary hover:bg-white/[0.055] hover:text-textPrimary"
      } disabled:cursor-not-allowed disabled:opacity-45`}
      title={title}
    >
      <Icon size={16} />
      <span className="text-sm font-medium">{label}</span>
    </button>
  );
}
