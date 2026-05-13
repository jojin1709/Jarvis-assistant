export default function ProviderDashboard({ providers = [] }) {
  return (
    <div className="grid gap-2">
      {providers.map((provider) => (
        <div key={provider.id || provider.name} className="rounded-xl border border-line px-3 py-2">
          <p className="text-sm font-medium text-textPrimary">{provider.label || provider.name}</p>
          <p className="text-xs text-textSecondary">{provider.available ? "Available" : "Needs setup"}</p>
        </div>
      ))}
    </div>
  );
}
