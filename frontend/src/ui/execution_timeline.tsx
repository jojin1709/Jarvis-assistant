export default function ExecutionTimeline({ events = [] }) {
  return (
    <div className="grid gap-2">
      {events.slice(0, 12).map((event) => (
        <div key={event.id || event.createdAt} className="rounded-xl border border-line px-3 py-2">
          <p className="text-sm font-medium text-textPrimary">{event.kind || event.event}</p>
          <p className="text-xs text-textSecondary">{event.createdAt}</p>
        </div>
      ))}
    </div>
  );
}
