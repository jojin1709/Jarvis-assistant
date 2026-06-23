import { useEffect, useState } from "react";
import { SkeletonCard } from "../components/SkeletonCard";

interface TraceEvent {
  id?: string;
  createdAt?: string;
  timestamp?: string;
  kind?: string;
  event?: string;
  message?: string;
  source?: string;
  level?: string;
}

export default function ExecutionTimeline({ events: propEvents = [] }: { events?: TraceEvent[] }) {
  const [events, setEvents] = useState<TraceEvent[]>(propEvents);
  const [loading, setLoading] = useState(propEvents.length === 0);

  useEffect(() => {
    if (propEvents.length > 0) {
      setEvents(propEvents);
      setLoading(false);
      return;
    }

    let active = true;
    fetch("/api/explainability/action-trace")
      .then((response) => response.json())
      .then((data) => {
        if (active) setEvents(data.trace || data.events || []);
      })
      .catch(() => {})
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [propEvents]);

  if (loading) {
    return (
      <div className="grid gap-2">
        {Array.from({ length: 4 }).map((_, index) => (
          <SkeletonCard key={index} lines={1} className="py-3" />
        ))}
      </div>
    );
  }

  if (!events.length) {
    return <p className="py-4 text-center text-sm text-textSecondary">No execution events yet. Run a task to see the trace.</p>;
  }

  return (
    <div className="grid max-h-96 gap-2 overflow-y-auto">
      {events.slice(0, 40).map((event, index) => {
        const level = event.level?.toLowerCase() || "info";
        const dot = level === "error" || level === "failed" ? "bg-red-400" : level === "success" ? "bg-emerald-400" : "bg-cyanCore";

        return (
          <div key={event.id || event.createdAt || event.timestamp || index} className="flex items-start gap-3 rounded-xl border border-line px-3 py-2">
            <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${dot}`} />
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-textPrimary">{event.message || event.kind || event.event || "Event"}</p>
              <p className="text-xs text-textSecondary">
                {event.createdAt || event.timestamp || ""}
                {event.source ? ` - ${event.source}` : ""}
              </p>
            </div>
          </div>
        );
      })}
    </div>
  );
}
