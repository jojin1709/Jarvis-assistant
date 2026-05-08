import { Languages } from "lucide-react";

const modes = [
  { id: "auto", label: "Auto" },
  { id: "en", label: "English" },
  { id: "ml", label: "Malayalam" },
];

export default function LanguageMode({ value, disabled, onChange }) {
  return (
    <div className="flex items-center gap-2 rounded-2xl border border-line bg-white/[0.035] px-2 py-1">
      <Languages size={15} className="text-textSecondary" />
      <div className="flex gap-1">
        {modes.map((mode) => (
          <button
            key={mode.id}
            type="button"
            disabled={disabled}
            onClick={() => onChange(mode.id)}
            className={`px-3 py-1.5 text-xs font-medium transition ${
              value === mode.id
                ? "bg-cyanCore/12 text-cyanCore"
                : "text-textSecondary hover:bg-white/[0.05] hover:text-textPrimary"
            } disabled:cursor-not-allowed disabled:opacity-50`}
            title={mode.id === "auto" ? "Auto detect speech language" : mode.id === "en" ? "Force English" : "Force Malayalam"}
          >
            {mode.label}
          </button>
        ))}
      </div>
    </div>
  );
}
