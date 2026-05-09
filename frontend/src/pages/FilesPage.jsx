import { useRef } from "react";
import { useOutletContext } from "react-router-dom";
import { FileText, FolderPlus, Search } from "lucide-react";

import FileIntake from "../components/FileIntake.jsx";

export default function FilesPage() {
  const runtime = useOutletContext();
  const inputRef = useRef(null);

  return (
    <div className="grid min-h-full gap-3 xl:grid-cols-[320px_minmax(0,1fr)]">
      <div className="grid gap-3">
        <FileIntake disabled={!runtime.backendOnline || runtime.busy} onUpload={runtime.handleUpload} />
        <section className="panel rounded-[24px] p-4">
          <h3 className="text-base font-semibold text-textPrimary">File actions</h3>
          <div className="mt-3 grid gap-2">
            <button type="button" disabled={!runtime.backendOnline || runtime.busy} className="panel-soft flex h-10 items-center gap-2 rounded-2xl px-3 text-sm text-textSecondary hover:text-textPrimary disabled:cursor-not-allowed disabled:opacity-40" onClick={() => inputRef.current?.click()}>
              <FolderPlus size={17} /> Upload and analyze
            </button>
            <button type="button" disabled={!runtime.backendOnline || runtime.busy} className="panel-soft flex h-10 items-center gap-2 rounded-2xl px-3 text-sm text-textSecondary hover:text-textPrimary disabled:cursor-not-allowed disabled:opacity-40" onClick={() => runtime.runTextFlow("create note")}>
              <FileText size={17} /> Create desktop note
            </button>
            <button type="button" disabled={!runtime.backendOnline || runtime.busy} className="panel-soft flex h-10 items-center gap-2 rounded-2xl px-3 text-sm text-textSecondary hover:text-textPrimary disabled:cursor-not-allowed disabled:opacity-40" onClick={() => runtime.runTextFlow("find file README")}>
              <Search size={17} /> Find files
            </button>
          </div>
        </section>
      </div>

      <section className="panel flex min-h-0 flex-col rounded-[24px] p-4">
        <input
          ref={inputRef}
          type="file"
          className="hidden"
          disabled={!runtime.backendOnline || runtime.busy}
          accept="text/*,image/*,audio/*,video/*,.pdf,.json,.csv,.md,.py,.js,.jsx,.ts,.tsx"
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) runtime.handleUpload(file);
            event.target.value = "";
          }}
        />
        <div className="mb-3 shrink-0">
          <h2 className="text-xl font-semibold tracking-[-0.03em] text-textPrimary">Files</h2>
          <p className="mt-1 text-sm text-textSecondary">AI file explorer, previews, recent uploads, and local file commands.</p>
        </div>

        <div className="min-h-0 flex-1 overflow-auto pr-1">
          <div className="grid gap-3">
          {runtime.uploads.length ? (
            runtime.uploads.map((file) => (
              <article key={`${file.path}-${file.filename}`} className="rounded-[22px] border border-line bg-white/[0.025] p-3">
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
            <div className="grid min-h-full place-items-center rounded-[24px] border border-line bg-white/[0.025] text-center">
              <div>
                <FileText className="mx-auto mb-3 text-cyanCore" size={34} />
                <p className="font-medium text-textPrimary">No files uploaded yet</p>
                <p className="mt-1 text-sm text-textSecondary">Drop a file into the intake panel to summarize it.</p>
              </div>
            </div>
          )}
          </div>
        </div>
      </section>
    </div>
  );
}
