import { useEffect, useMemo, useState } from "react";
import { useOutletContext } from "react-router-dom";
import { AppWindow, CheckCircle2, FolderOpen, Plus, RefreshCcw, Search, ShieldCheck, XCircle } from "lucide-react";

import { API_BASE, getPermissions, getSystemApps, scanSystemAppsFolder, updatePermissions } from "../services/api.js";

function normalizeApp(value) {
  return String(value || "").toLowerCase().replaceAll("-", " ").replaceAll("_", " ").trim().replace(/\s+/g, " ");
}

export default function AppsPage() {
  const runtime = useOutletContext();
  const [query, setQuery] = useState("");
  const [manualApp, setManualApp] = useState("");
  const [localApps, setLocalApps] = useState([]);
  const [saving, setSaving] = useState(false);
  const [savingApp, setSavingApp] = useState("");
  const [localAllowedApps, setLocalAllowedApps] = useState([]);
  const [localCustomApps, setLocalCustomApps] = useState([]);
  const [loadingApps, setLoadingApps] = useState(false);
  const [scanningFolder, setScanningFolder] = useState(false);
  const [failedIcons, setFailedIcons] = useState(() => new Set());
  const allowedApps = localAllowedApps;
  const allowedSet = useMemo(() => new Set(allowedApps.map(normalizeApp)), [allowedApps]);

  useEffect(() => {
    setLocalApps(runtime.installedApps || []);
  }, [runtime.installedApps]);

  useEffect(() => {
    const next = runtime.permissions?.allowedApps;
    if (Array.isArray(next)) setLocalAllowedApps(next);
  }, [runtime.permissions?.allowedApps]);

  useEffect(() => {
    const next = runtime.permissions?.customApps;
    if (Array.isArray(next)) setLocalCustomApps(next);
  }, [runtime.permissions?.customApps]);

  useEffect(() => {
    refreshApps();
    // Run once when the page opens; background polling still keeps the shared runtime fresh.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const apps = useMemo(() => {
    const list = localApps || [];
    const filtered = query.trim()
      ? list.filter((app) => normalizeApp(app.label).includes(normalizeApp(query)))
      : list;
    return [...filtered].sort((a, b) => {
      const allowedDelta = Number(allowedSet.has(normalizeApp(b.label))) - Number(allowedSet.has(normalizeApp(a.label)));
      if (allowedDelta) return allowedDelta;
      return String(a.label).localeCompare(String(b.label));
    });
  }, [localApps, query, allowedSet]);

  async function refreshApps() {
    setLoadingApps(true);
    try {
      const [appsResult, permissionsResult] = await Promise.all([getSystemApps(), getPermissions()]);
      setLocalApps(appsResult.apps || []);
      runtime.setInstalledApps(appsResult.apps || []);
      const permissions = permissionsResult.permissions || null;
      runtime.setPermissions(permissions);
      setLocalAllowedApps(Array.isArray(permissions?.allowedApps) ? permissions.allowedApps : []);
      setLocalCustomApps(Array.isArray(permissions?.customApps) ? permissions.customApps : []);
    } catch (error) {
      runtime.addExecutionLog({ message: error?.message || "Could not refresh apps.", level: "error" });
    } finally {
      setLoadingApps(false);
    }
  }

  async function saveAllowedApps(next, message, nextCustomApps = localCustomApps) {
    const cleanCustomApps = dedupeCustomApps(nextCustomApps);
    setLocalAllowedApps(next);
    setLocalCustomApps(cleanCustomApps);
    runtime.setPermissions({ ...(runtime.permissions || {}), allowedApps: next, customApps: cleanCustomApps });
    setSaving(true);
    try {
      const result = await updatePermissions({ allowedApps: next, customApps: cleanCustomApps });
      runtime.setPermissions(result.permissions);
      runtime.addExecutionLog({ message, level: "success" });
    } catch (error) {
      const rollback = runtime.permissions?.allowedApps || [];
      const rollbackCustomApps = runtime.permissions?.customApps || [];
      setLocalAllowedApps(rollback);
      setLocalCustomApps(rollbackCustomApps);
      runtime.setPermissions({ ...(runtime.permissions || {}), allowedApps: rollback, customApps: rollbackCustomApps });
      runtime.addExecutionLog({ message: error?.message || "Could not update app permissions.", level: "error" });
    } finally {
      setSaving(false);
      setSavingApp("");
    }
  }

  async function setAllowed(app, allowed) {
    const label = app.label;
    const normalized = normalizeApp(label);
    const next = allowed
      ? [...allowedApps, label]
      : allowedApps.filter((item) => normalizeApp(item) !== normalized);
    const nextCustomApps = allowed ? dedupeCustomApps([...localCustomApps, customAppFromSystemApp(app)].filter(Boolean)) : localCustomApps;
    setSavingApp(label);
    await saveAllowedApps(dedupeApps(next), `${label} ${allowed ? "enabled" : "disabled"} for Jarvis.`, nextCustomApps);
  }

  async function allowAllShown() {
    await saveAllowedApps(
      dedupeApps([...allowedApps, ...apps.map((app) => app.label)]),
      "Shown apps enabled for Jarvis.",
      dedupeCustomApps([...localCustomApps, ...apps.map(customAppFromSystemApp).filter(Boolean)]),
    );
  }

  async function blockAllShown() {
    const shown = new Set(apps.map((app) => normalizeApp(app.label)));
    await saveAllowedApps(allowedApps.filter((label) => !shown.has(normalizeApp(label))), "Shown apps disabled for Jarvis.");
  }

  async function addManualApp(event) {
    event.preventDefault();
    const label = manualApp.trim();
    if (!label) return;
    setManualApp("");
    await saveAllowedApps(dedupeApps([...allowedApps, label]), `${label} manually enabled for Jarvis.`);
  }

  async function browseAppFolder() {
    if (!window.jxJarvis?.chooseFolder) {
      runtime.addExecutionLog({ message: "Folder picker is available only inside the desktop app.", level: "error" });
      return;
    }
    const selected = await window.jxJarvis.chooseFolder("Choose app folder");
    if (!selected) return;

    setScanningFolder(true);
    try {
      const result = await scanSystemAppsFolder(selected);
      const foundApps = result.apps || [];
      const mergedApps = mergeApps(localApps, foundApps);
      const nextCustomApps = dedupeCustomApps([...localCustomApps, ...foundApps.map(customAppFromSystemApp).filter(Boolean)]);
      setLocalApps(mergedApps);
      setLocalCustomApps(nextCustomApps);
      runtime.setInstalledApps(mergedApps);
      const permissions = { ...(runtime.permissions || {}), customApps: nextCustomApps };
      runtime.setPermissions(permissions);
      await updatePermissions({ customApps: nextCustomApps });
      runtime.addExecutionLog({ message: `${foundApps.length} app(s) found in the selected folder.`, level: "success" });
    } catch (error) {
      runtime.addExecutionLog({ message: error?.message || "Could not scan the selected folder.", level: "error" });
    } finally {
      setScanningFolder(false);
    }
  }

  return (
    <section className="panel min-h-full rounded-[24px] p-4">
      <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold tracking-[-0.03em] text-textPrimary">Apps</h2>
          <p className="mt-1 text-sm text-textSecondary">Choose which Windows apps Jarvis is allowed to open and control.</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            disabled={!apps.length || saving}
            onClick={allowAllShown}
            className="rounded-2xl border border-cyanCore/25 bg-cyanCore/10 px-3 py-2 text-sm font-medium text-cyanCore disabled:opacity-45"
          >
            Allow all shown
          </button>
          <button
            type="button"
            disabled={!apps.length || saving}
            onClick={blockAllShown}
            className="rounded-2xl border border-line bg-white/[0.035] px-3 py-2 text-sm text-textSecondary disabled:opacity-45"
          >
            Block shown
          </button>
          <button
            type="button"
            disabled={scanningFolder}
            onClick={browseAppFolder}
            className="inline-flex items-center gap-2 rounded-2xl border border-line bg-white/[0.035] px-3 py-2 text-sm text-textSecondary disabled:opacity-45"
          >
            <FolderOpen size={15} />
            Browse folder
          </button>
          <button
            type="button"
            disabled={loadingApps}
            onClick={refreshApps}
            className="inline-flex items-center gap-2 rounded-2xl border border-line bg-white/[0.035] px-3 py-2 text-sm text-textSecondary disabled:opacity-45"
          >
            <RefreshCcw size={15} className={loadingApps ? "animate-spin" : ""} />
            Refresh
          </button>
          <div className="rounded-2xl border border-line bg-white/[0.035] px-3 py-2 text-sm text-textSecondary">
            {allowedApps.length} enabled / {localApps.length} found
          </div>
        </div>
      </div>

      <div className="mb-4 flex items-center gap-2 rounded-[20px] border border-line bg-white/[0.035] px-3 py-2">
        <Search size={17} className="text-textSecondary" />
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          className="min-w-0 flex-1 bg-transparent py-2 text-sm text-textPrimary outline-none placeholder:text-textSecondary"
          placeholder="Search apps like Chrome, VS Code, Photoshop, Terminal..."
        />
      </div>

      <form className="mb-4 grid gap-2 rounded-[20px] border border-line bg-white/[0.025] p-3 sm:grid-cols-[minmax(0,1fr)_auto]" onSubmit={addManualApp}>
        <input
          value={manualApp}
          onChange={(event) => setManualApp(event.target.value)}
          className="min-w-0 rounded-2xl border border-line bg-[#070B14]/70 px-3 py-2 text-sm text-textPrimary outline-none placeholder:text-textSecondary"
          placeholder="Manually allow app name, e.g. Adobe Photoshop 2025"
        />
        <button
          type="submit"
          disabled={!manualApp.trim() || saving}
          className="inline-flex h-10 items-center justify-center gap-2 rounded-2xl bg-cyanCore px-4 text-sm font-semibold text-[#021018] disabled:opacity-45"
        >
          <Plus size={16} />
          Add allowed app
        </button>
      </form>

      <div className="grid gap-3 md:grid-cols-2 2xl:grid-cols-3">
        {apps.map((app) => {
          const allowed = allowedSet.has(normalizeApp(app.label));
          const iconKey = app.path || app.id || app.label;
          const iconSrc = app.iconUrl && !failedIcons.has(iconKey) ? `${API_BASE}${app.iconUrl}` : "";
          return (
            <article key={app.id || app.label} className="rounded-[22px] border border-line bg-white/[0.025] p-3">
              <div className="flex items-start justify-between gap-3">
                <div className="flex min-w-0 items-start gap-3">
                  <div className={`grid h-10 w-10 shrink-0 place-items-center rounded-2xl ${allowed ? "bg-cyanCore/10 text-cyanCore" : "bg-white/[0.055] text-textSecondary"}`}>
                    {iconSrc ? (
                      <img
                        src={iconSrc}
                        alt=""
                        className="h-6 w-6 rounded-md object-contain"
                        onError={() => setFailedIcons((current) => new Set([...current, iconKey]))}
                      />
                    ) : (
                      <AppWindow size={18} />
                    )}
                  </div>
                  <div className="min-w-0">
                    <h3 className="truncate text-sm font-semibold text-textPrimary">{app.label}</h3>
                    <p className="mt-1 truncate text-xs capitalize text-textSecondary">
                      {app.source || "app"} {app.running ? "- running" : app.installed ? "- installed" : "- fallback"}
                    </p>
                    {app.path ? <p className="mt-1 truncate text-[11px] text-textSecondary/70">{app.path}</p> : null}
                  </div>
                </div>
                {allowed ? <CheckCircle2 size={18} className="shrink-0 text-cyanCore" /> : <XCircle size={18} className="shrink-0 text-textSecondary" />}
              </div>

              <button
                type="button"
                disabled={savingApp === app.label}
                onClick={() => setAllowed(app, !allowed)}
                className={`mt-3 flex h-10 w-full items-center justify-center gap-2 rounded-2xl border text-sm font-medium transition disabled:opacity-45 ${
                  allowed
                    ? "border-cyanCore/25 bg-cyanCore/10 text-cyanCore hover:bg-cyanCore/15"
                    : "border-line bg-white/[0.025] text-textSecondary hover:text-textPrimary"
                }`}
              >
                <ShieldCheck size={16} />
                {allowed ? "Allowed" : "Allow Jarvis"}
              </button>
            </article>
          );
        })}
      </div>

      {!apps.length ? (
        <div className="mt-4 rounded-[22px] border border-line bg-white/[0.025] p-4 text-sm text-textSecondary">
          No apps found. Try clearing the search, refreshing, or browsing a folder that contains app shortcuts or .exe files.
        </div>
      ) : null}
    </section>
  );
}

function mergeApps(...groups) {
  const seen = new Set();
  const result = [];
  for (const group of groups) {
    for (const app of group || []) {
      const key = `${normalizeApp(app.label)}::${String(app.path || "").toLowerCase()}`;
      if (!app?.label || seen.has(key)) continue;
      seen.add(key);
      result.push(app);
    }
  }
  return result;
}

function customAppFromSystemApp(app) {
  if (!app?.label || !app?.path) return null;
  return {
    label: app.label,
    path: app.path,
    kind: app.kind || (String(app.path).toLowerCase().endsWith(".lnk") ? "shortcut" : "exe"),
    source: app.source || "custom",
  };
}

function dedupeCustomApps(values) {
  const seen = new Set();
  const result = [];
  for (const value of values || []) {
    if (!value?.label || !value?.path) continue;
    const key = `${normalizeApp(value.label)}::${String(value.path).toLowerCase()}`;
    if (seen.has(key)) continue;
    seen.add(key);
    result.push(customAppFromSystemApp(value));
  }
  return result;
}

function dedupeApps(values) {
  const seen = new Set();
  const result = [];
  for (const value of values) {
    const normalized = normalizeApp(value);
    if (!normalized || seen.has(normalized)) continue;
    seen.add(normalized);
    result.push(value);
  }
  return result;
}
