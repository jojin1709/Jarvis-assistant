import { useEffect, useState } from "react";

interface MemoryItem {
  id?: number | string;
  text?: string;
  summary?: string;
  title?: string;
  content?: string;
  kind?: string;
  createdAt?: string;
  created_at?: string;
}

export default function MemoryExplorer({ memories: propMemories = [] }: { memories?: MemoryItem[] }) {
  const [memories, setMemories] = useState<MemoryItem[]>(propMemories);
  const [loading, setLoading] = useState(propMemories.length === 0);
  const [search, setSearch] = useState("");

  useEffect(() => {
    if (propMemories.length > 0) {
      setMemories(propMemories);
      setLoading(false);
      return;
    }
    let active = true;
    fetch("/api/memory")
      .then((response) => response.json())
      .then((data) => {
        if (active) setMemories(data.recent || data.memories || []);
      })
      .catch(() => {})
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [propMemories]);

  const filtered = memories.filter((memory) => {
    const text = `${memory.text || ""} ${memory.summary || ""} ${memory.title || ""} ${memory.content || ""}`.toLowerCase();
    return text.includes(search.toLowerCase());
  });

  if (loading) return <div className="h-10 animate-pulse rounded-xl bg-white/5" />;

  return (
    <div className="grid gap-2">
      <input
        value={search}
        onChange={(event) => setSearch(event.target.value)}
        placeholder="Search memory..."
        className="w-full rounded-2xl border border-line bg-[#070B14]/70 px-4 py-2 text-sm text-textPrimary outline-none placeholder:text-textSecondary"
      />
      {filtered.length === 0 ? (
        <p className="py-4 text-center text-sm text-textSecondary">{search ? "No matches." : "No memories yet."}</p>
      ) : (
        <div className="grid max-h-72 gap-2 overflow-y-auto">
          {filtered.slice(0, 20).map((memory, index) => (
            <div key={memory.id || index} className="rounded-xl border border-line px-3 py-2">
              <p className="truncate text-sm font-medium text-textPrimary">{memory.title || memory.kind || "Memory item"}</p>
              <p className="mt-1 line-clamp-2 text-sm text-textSecondary">{memory.text || memory.summary || memory.content || ""}</p>
              <p className="mt-1 text-xs text-textSecondary">{memory.createdAt || memory.created_at || ""}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
