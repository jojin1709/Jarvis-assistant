import { useRef } from "react";
import { useOutletContext } from "react-router-dom";
import { FileText, FolderPlus, Trash2 } from "lucide-react";

import FileIntake from "../components/FileIntake.jsx";

export default function FilesPage() {
  const runtime = useOutletContext();
  const inputRef = useRef(null);

  return (
    <div className="grid gap-4 xl:grid-cols-[360px_minmax(0,1fr)]">
      <div className="space-y-4">
        <FileIntake disabled={!runtime.backendOnline || runtime.busy} onUpload={runtime.handleUpload} />
        <section className="panel rounded-[28px] p-5">
          <h3 className="text-base font-semibold text-textPrimary">File actions</h3>
          <div className="mt-4 grid gap-2">
            <button className="panel-soft flex h-12 items-center gap-3 rounded-2xl px-3 text-sm text-textSecondary hover:text-textPrimary" onClick={() => inputRef.current?.click()}>
              <FolderPlus size={17} /> Upload and analyze
            </button>
            <button className="panel-soft flex h-12 items-center gap-3 rounded-2xl px-3 text-sm text-textSecondary hover:text-textPrimary" onClick={() => runtime.runTextFlow("create note")}>
              <FileText size={17} /> Create desktop note
            </button>
            <button className="panel-soft flex h-12 items-center gap-3 rounded-2xl px-3 text-sm text-textSecondary hover:text-textPrimary" onClick={() => runtime.runTextFlow("find file README")}>
              <Trash2 size={17} /> Find files
            </button>
          </div>
        </section>
      </div>

      <section className="panel rounded-[28px] p-5">
        <input
          ref={inputRef}
          type="file"
          className="hidden"
          accept="text/*,image/*,audio/*,video/*,.pdf,.json,.csv,.md,.py,.js,.jsx,.ts,.tsx"
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) runtime.handleUpload(file);
            event.target.value = "";
          }}
        />
        <div className="mb-5">
          <h2 className="text-2xl font-semibold tracking-[-0.03em] text-textPrimary">Files</h2>
          <p className="mt-1 text-sm text-textSecondary">AI file explorer, previews, recent uploads, and local file commands.</p>
        </div>

        <div className="grid gap-3">
          {runtime.uploads.length ? (
            runtime.uploads.map((file) => (
              <article key={`${file.path}-${file.filename}`} className="rounded-[24px] border border-line bg-white/[0.025] p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="truncate font-medium text-textPrimary">{file.filename}</p>
                    <p className="mt-1 text-sm text-textSecondary">{file.mime_type} - {Math.round((file.size || 0) / 1024)} KB</p>
                  </div>
                  <span className="rounded-full border border-line px-2.5 py-1 text-xs text-textSecondary">
                    {file.document_intelligence_used ? "Document AI" : file.text_indexed ? "Indexed" : "Stored"}
                  </span>
                </div>
                <p className="mt-3 line-clamp-2 text-sm leading-6 text-textSecondary">{file.summary}</p>
              </article>
            ))
          ) : (
            <div className="grid min-h-72 place-items-center rounded-[28px] border border-line bg-white/[0.025] text-center">
              <div>
                <FileText className="mx-auto mb-3 text-cyanCore" size={34} />
                <p className="font-medium text-textPrimary">No files uploaded yet</p>
                <p className="mt-1 text-sm text-textSecondary">Drop a file into the intake panel to summarize it.</p>
              </div>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
