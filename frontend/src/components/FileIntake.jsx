import { FileUp, HardDriveUpload, Loader2 } from "lucide-react";
import { useRef, useState } from "react";

const mediaTypes = ["video", "image", "audio", "pdf", "code", "text"];

export default function FileIntake({ disabled, onUpload }) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);

  function pickFile() {
    inputRef.current?.click();
  }

  function handleFiles(files) {
    const file = files?.[0];
    if (file) onUpload(file);
  }

  return (
    <section
      className={`hud-panel group relative overflow-hidden p-4 ${dragging ? "border-cyanSoft bg-cyanCore/10" : ""}`}
      onDragOver={(event) => {
        event.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(event) => {
        event.preventDefault();
        setDragging(false);
        handleFiles(event.dataTransfer.files);
      }}
    >
      <input
        ref={inputRef}
        type="file"
        className="hidden"
        onChange={(event) => handleFiles(event.target.files)}
        accept="text/*,image/*,audio/*,video/*,.pdf,.json,.csv,.md,.py,.js,.jsx,.ts,.tsx"
      />
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.28em] text-cyanSoft">File Intake</p>
          <p className="mt-2 text-sm leading-relaxed text-white/65">Multimedia / code / documents</p>
        </div>
        <HardDriveUpload className="text-cyanSoft" size={24} />
      </div>

      <button
        type="button"
        disabled={disabled}
        onClick={pickFile}
        className="mt-4 flex h-12 w-full items-center justify-center gap-2 border border-cyanCore/45 bg-cyanCore/10 text-sm font-semibold uppercase tracking-[0.2em] text-cyanSoft transition hover:bg-cyanCore/20 disabled:opacity-40"
      >
        {disabled ? <Loader2 className="animate-spin" size={18} /> : <FileUp size={18} />}
        Upload
      </button>

      <div className="mt-4 grid grid-cols-3 gap-2">
        {mediaTypes.map((type) => (
          <span key={type} className="border border-cyanCore/15 bg-black/25 px-2 py-1 text-center text-[11px] uppercase tracking-[0.16em] text-cyanSoft/60">
            {type}
          </span>
        ))}
      </div>
    </section>
  );
}
