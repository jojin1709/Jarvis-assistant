import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export default function MarkdownMessage({ children }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        p: ({ children: content }) => <p className="mb-3 leading-7 last:mb-0">{content}</p>,
        ul: ({ children: content }) => <ul className="mb-3 list-disc space-y-1 pl-5">{content}</ul>,
        ol: ({ children: content }) => <ol className="mb-3 list-decimal space-y-1 pl-5">{content}</ol>,
        code: ({ inline, children: content }) =>
          inline ? (
            <code className="rounded-md bg-white/[0.06] px-1.5 py-0.5 text-cyanCore">{content}</code>
          ) : (
            <code className="block overflow-auto rounded-2xl border border-line bg-[#050914] p-4 text-sm text-textPrimary">
              {content}
            </code>
          ),
        pre: ({ children: content }) => <pre className="mb-3">{content}</pre>,
        a: ({ children: content, href }) => (
          <a className="text-cyanCore underline decoration-cyanCore/30 underline-offset-4" href={href} target="_blank" rel="noreferrer">
            {content}
          </a>
        ),
      }}
    >
      {children || ""}
    </ReactMarkdown>
  );
}
