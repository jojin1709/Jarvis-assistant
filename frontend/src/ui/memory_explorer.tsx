export default function MemoryExplorer({ memories = [] }) {
  return (
    <div className="grid gap-2">
      {memories.slice(0, 8).map((memory, index) => (
        <div key={memory.id || index} className="rounded-xl border border-line px-3 py-2 text-sm text-textSecondary">
          {memory.text || memory.summary || "Memory item"}
        </div>
      ))}
    </div>
  );
}
