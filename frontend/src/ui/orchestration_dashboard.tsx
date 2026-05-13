import { Activity, Cloud, Gauge, RadioTower } from "lucide-react";

export default function OrchestrationDashboard({ production = {} }) {
  const sync = production.sync || {};
  const telemetry = production.telemetry || {};
  const performance = production.performance || {};
  const remote = production.remote || {};

  return (
    <div className="grid gap-2">
      <Tile icon={Cloud} label="Cloud sync" value={sync.mode || "local-first"} detail={sync.encryption?.enabled ? "encrypted backups" : "encryption unavailable"} />
      <Tile icon={Activity} label="Telemetry" value={telemetry.config?.enabled ? "Enabled" : "Off"} detail={telemetry.localOnly ? "local diagnostics only" : "sharing allowed"} />
      <Tile icon={Gauge} label="Performance" value={performance.mode || "balanced"} detail={`${performance.plan?.maxParallelTasks || 1} parallel task(s)`} />
      <Tile icon={RadioTower} label="Remote agents" value={remote.remote?.enabled ? "Enabled" : "Optional"} detail={`${remote.remote?.workers?.length || 0} worker(s)`} />
    </div>
  );
}

function Tile({ icon: Icon, label, value, detail }) {
  return (
    <div className="rounded-2xl border border-line bg-white/[0.025] px-3 py-2">
      <div className="flex items-center gap-3">
        <div className="grid h-8 w-8 place-items-center rounded-xl bg-cyanCore/10 text-cyanCore">
          <Icon size={16} />
        </div>
        <div className="min-w-0">
          <p className="text-sm font-medium text-textPrimary">{label}</p>
          <p className="truncate text-sm text-textSecondary">
            {value} · {detail}
          </p>
        </div>
      </div>
    </div>
  );
}
