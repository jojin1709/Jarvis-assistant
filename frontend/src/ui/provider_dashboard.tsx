import { useEffect, useState } from "react";

interface Provider {
  id?: string;
  name?: string;
  label?: string;
  available?: boolean;
  enabled?: boolean;
  configured?: boolean;
  model?: string;
}

export default function ProviderDashboard({ providers: propProviders = [] }: { providers?: Provider[] }) {
  const [providers, setProviders] = useState<Provider[]>(propProviders);
  const [loading, setLoading] = useState(propProviders.length === 0);

  useEffect(() => {
    if (propProviders.length > 0) {
      setProviders(propProviders);
      setLoading(false);
      return;
    }

    let active = true;
    fetch("/api/providers")
      .then((response) => response.json())
      .then((data) => {
        if (active) setProviders(data.providers || []);
      })
      .catch(() => {})
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [propProviders]);

  if (loading) return <div className="h-12 animate-pulse rounded-xl bg-white/5" />;

  if (!providers.length) {
    return <p className="py-4 text-center text-sm text-textSecondary">No providers configured yet.</p>;
  }

  return (
    <div className="grid gap-2">
      {providers.map((provider) => {
        const ready = provider.available || provider.configured || provider.enabled;
        return (
          <div key={provider.id || provider.name} className="rounded-xl border border-line px-3 py-2">
            <div className="flex items-center justify-between gap-2">
              <p className="truncate text-sm font-medium text-textPrimary">{provider.label || provider.name || provider.id}</p>
              <span className={`rounded-full px-2 py-0.5 text-xs ${ready ? "bg-emerald-400/10 text-emerald-200" : "bg-amber-400/10 text-amber-200"}`}>
                {ready ? "Available" : "Needs setup"}
              </span>
            </div>
            {provider.model ? <p className="mt-1 truncate text-xs text-textSecondary">{provider.model}</p> : null}
          </div>
        );
      })}
    </div>
  );
}
