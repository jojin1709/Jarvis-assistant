import { Languages } from "lucide-react";

const modes = [
  { id: "auto", label: "Auto" },
  { id: "en", label: "EN" },
  { id: "ml", label: "ML" },
];

export default function LanguageMode({ value, disabled, onChange }) {
  return (
    <div className="flex items-center gap-2 rounded-full border border-cyanCore/20 bg-black/35 px-2 py-1 backdrop-blur">
      <Languages size={15} className="text-cyanSoft/75" />
      <div className="flex gap-1">
        {modes.map((mode) => (
          <button
            key={mode.id}
            type="button"
            disabled={disabled}
            onClick={() => onChange(mode.id)}
            className={`language-chip ${value === mode.id ? "active" : ""}`}
            title={mode.id === "auto" ? "Auto detect speech language" : mode.id === "en" ? "Force English" : "Force Malayalam"}
          >
            {mode.label}
          </button>
        ))}
      </div>
    </div>
  );
}
