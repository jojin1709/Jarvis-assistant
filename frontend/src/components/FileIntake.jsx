import { FileUp, HardDriveUpload, Loader2 } from "lucide-react";
import { useRef, useState } from "react";

const mediaTypes = ["video", "image", "audio", "pdf", "code", "text"];

export default function FileIntake({ disabled, onUpload }) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);

  function pickFile() {
    if (disabled) return;
    inputRef.current?.click();
  }

  function handleFiles(files) {
    if (disabled) return;
    const file = files?.[0];
    if (file) onUpload(file);
  }

  return (
    <section
      className={`panel group relative overflow-hidden rounded-[24px] p-4 ${dragging ? "border-cyanCore/30 bg-cyanCore/10" : ""}`}
      onDragOver={(event) => {
        if (disabled) return;
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
          <p className="text-sm font-semibold text-textPrimary">File intake</p>
          <p className="mt-1 text-sm leading-relaxed text-textSecondary">Multimedia, code, and documents</p>
        </div>
        <HardDriveUpload className="text-cyanCore" size={22} />
      </div>

      <button
        type="button"
        disabled={disabled}
        onClick={pickFile}
        className="mt-3 flex h-10 w-full items-center justify-center gap-2 rounded-2xl border border-cyanCore/20 bg-cyanCore/10 text-sm font-semibold text-cyanCore transition hover:bg-cyanCore/15 disabled:opacity-40"
      >
        {disabled ? <Loader2 className="animate-spin" size={18} /> : <FileUp size={18} />}
        Upload
      </button>

      <div className="mt-3 grid grid-cols-3 gap-2">
        {mediaTypes.map((type) => (
          <span key={type} className="rounded-xl border border-line bg-white/[0.03] px-2 py-1 text-center text-xs text-textSecondary">
            {type}
          </span>
        ))}
      </div>
    </section>
  );
}
