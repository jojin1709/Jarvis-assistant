import { useEffect, useState } from "react";
import { useOutletContext } from "react-router-dom";
import {
  Activity,
  AppWindow,
  Brain,
  BrainCircuit,
  Cloud,
  DatabaseZap,
  Download,
  Eye,
  EyeOff,
  FolderCheck,
  FolderLock,
  Globe2,
  HardDrive,
  KeyRound,
  Linkedin,
  LockKeyhole,
  Mic2,
  Palette,
  Plus,
  RefreshCcw,
  ShieldCheck,
  Sparkles,
  Terminal,
  Trash2,
  X,
  Zap,
} from "lucide-react";

import {
  backupMemoryStorage,
  clearBrainMemory,
  clearMemory,
  exportMemory,
  getProviders,
  removeProviderKey,
  saveProviderKey,
  setupMemoryStorage,
  testProvider,
  updateProviderConfig,
  updatePermissions,
  updateProfile,
} from "../services/api.js";

const providers = ["auto", "groq", "openai", "claude", "ollama", "gemini", "openrouter", "local_llamacpp"];

const fallbackPermissions = {
  fullSystemAccess: false,
  safeMode: false,
  autoExecutionMode: true,
  memoryEnabled: true,
  controls: {
    fileSystemAccess: true,
    browserControl: true,
    terminalExecution: false,
    appControl: true,
    voiceActivation: true,
    automationMode: false,
    internetAccess: true,
    backgroundListening: true,
  },
  confirmations: { low: false, medium: true, high: true },
  protectedFolders: [],
  protectedFiles: [],
  protectedApps: [],
  allowedWorkspaces: [],
};

const accessControls = [
  ["fileSystemAccess", "File System Access", FolderCheck],
  ["browserControl", "Browser Control", Globe2],
  ["terminalExecution", "Terminal Execution", Terminal],
  ["appControl", "App Control", AppWindow],
  ["voiceActivation", "Voice Activation", Mic2],
  ["automationMode", "Automation Mode", Zap],
  ["internetAccess", "Internet Access", Globe2],
  ["backgroundListening", "Background Listening", Activity],
];

export default function SettingsPage() {
  const runtime = useOutletContext();
  const permissions = runtime.permissions || fallbackPermissions;
  const [saving, setSaving] = useState(false);
  const [openAtLogin, setOpenAtLogin] = useState(false);
  const [memoryPath, setMemoryPath] = useState("");
  const [providerKeys, setProviderKeys] = useState({});
  const [visibleKeys, setVisibleKeys] = useState({});
  const [providerTests, setProviderTests] = useState({});

  useEffect(() => {
    let active = true;
    window.jxJarvis?.getOpenAtLogin?.().then((enabled) => {
      if (active) setOpenAtLogin(Boolean(enabled));
    });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    setMemoryPath(runtime.memoryStorage?.path || runtime.profile?.memory_storage_path || "");
  }, [runtime.memoryStorage?.path, runtime.profile?.memory_storage_path]);

  async function patchPermissions(patch) {
    setSaving(true);
    try {
      const result = await updatePermissions(patch);
      runtime.setPermissions(result.permissions);
      runtime.addExecutionLog({ message: "Permission settings updated", level: "success" });
    } catch (error) {
      runtime.addExecutionLog({ message: error.message || "Permission update failed", level: "error" });
    } finally {
      setSaving(false);
    }
  }

  async function handleClearMemory() {
    const result = await clearMemory();
    runtime.setResponse(result.response);
    runtime.addExecutionLog({ message: result.response, level: "success" });
  }

  async function handleExportMemory() {
    const data = await exportMemory();
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "jx-jarvis-memory-export.json";
    link.click();
    URL.revokeObjectURL(url);
    runtime.addExecutionLog({ message: "Memory exported", level: "success" });
  }

  async function toggleOpenAtLogin() {
    if (!window.jxJarvis?.setOpenAtLogin) return;
    const enabled = await window.jxJarvis.setOpenAtLogin(!openAtLogin);
    setOpenAtLogin(Boolean(enabled));
  }

  async function patchProfile(patch) {
    const result = await updateProfile(patch);
    runtime.setProfile(result.profile);
    runtime.setMemory({ ...(runtime.memory || {}), ...result.profile });
  }

  async function chooseMemoryFolder() {
    const selected = await window.jxJarvis?.chooseFolder?.();
    if (selected) setMemoryPath(selected);
  }

  async function saveMemoryFolder() {
    const result = await setupMemoryStorage(memoryPath);
    runtime.setMemoryStorage(result.memory);
    runtime.setProfile(result.profile);
    runtime.addExecutionLog({ message: `Memory storage configured: ${result.memory.path}`, level: "success" });
  }

  async function backupBrain() {
    const result = await backupMemoryStorage();
    runtime.addExecutionLog({ message: `Memory backup created: ${result.backup.path}`, level: "success" });
  }

  async function clearBrain() {
    const result = await clearBrainMemory();
    runtime.setMemoryStorage(result.memory);
    runtime.addExecutionLog({ message: "Brain storage cleared", level: "warning" });
  }

  async function refreshProviders() {
    const result = await getProviders();
    runtime.setAiProviders(result.providers || [], result.config || null, result.ollamaModels || []);
  }

  async function patchProviderConfig(patch) {
    const result = await updateProviderConfig(patch);
    runtime.setAiProviders(result.providers || [], result.config || null, result.ollamaModels || []);
    runtime.addExecutionLog({ message: "AI provider settings updated", level: "success" });
  }

  async function saveKey(provider) {
    const apiKey = (providerKeys[provider] || "").trim();
    if (!apiKey) return;
    const result = await saveProviderKey(provider, apiKey);
    setProviderKeys((current) => ({ ...current, [provider]: "" }));
    runtime.setAiProviders(result.providers || [], result.config || null, result.ollamaModels || []);
    runtime.addExecutionLog({ message: `AI provider key saved: ${provider}`, level: "success" });
  }

  async function removeKey(provider) {
    const result = await removeProviderKey(provider);
    runtime.setAiProviders(result.providers || [], result.config || null, result.ollamaModels || []);
    runtime.addExecutionLog({ message: `AI provider key removed: ${provider}`, level: "warning" });
  }

  async function runProviderTest(provider, model) {
    setProviderTests((current) => ({ ...current, [provider]: { status: "running", message: "Testing..." } }));
    const result = await testProvider(provider, model);
    setProviderTests((current) => ({
      ...current,
      [provider]: {
        status: result.ok ? "success" : "error",
        message: result.ok ? `${result.message || "Online"} (${result.latencyMs || 0} ms)` : result.error,
      },
    }));
  }

  return (
    <div className="space-y-4">
      <div className="grid gap-4 xl:grid-cols-2">
        <SettingsCard icon={Sparkles} title="Profile & Preferences">
          <label className="text-sm text-textSecondary" htmlFor="profile-name">Name</label>
          <input
            id="profile-name"
            defaultValue={runtime.profile?.user_name || runtime.userName}
            onBlur={(event) => patchProfile({ user_name: event.target.value })}
            className="mt-2 w-full rounded-2xl border border-line bg-[#070B14]/70 px-3 py-2 text-sm text-textPrimary outline-none"
          />
          <div className="mt-3 grid grid-cols-2 gap-2">
            {["Developer", "Student", "Creator", "Researcher", "Cybersecurity", "General Use"].map((type) => (
              <button
                key={type}
                type="button"
                onClick={() => patchProfile({ user_type: type })}
                className={`rounded-2xl border border-line px-3 py-2 text-sm ${
                  (runtime.profile?.user_type || "General Use") === type ? "bg-cyanCore/10 text-cyanCore" : "text-textSecondary hover:text-textPrimary"
                }`}
              >
                {type}
              </button>
            ))}
          </div>
          <div className="mt-4">
            <label className="text-sm text-textSecondary" htmlFor="personality">Assistant personality</label>
            <select
              id="personality"
              value={runtime.profile?.personality || "professional"}
              onChange={(event) => patchProfile({ personality: event.target.value })}
              className="mt-2 w-full rounded-2xl border border-line bg-[#070B14]/70 px-3 py-2 text-sm text-textPrimary outline-none"
            >
              <option value="professional">Professional</option>
              <option value="concise">Concise</option>
              <option value="friendly">Friendly</option>
              <option value="technical">Technical</option>
            </select>
          </div>
        </SettingsCard>

        <SettingsCard icon={Palette} title="Appearance">
          <Toggle label="Dark premium theme" checked={runtime.settings.theme === "dark"} onChange={() => runtime.updateSettings({ theme: "dark" })} />
          <Toggle label="Startup audio" checked={runtime.settings.startupAudio} onChange={() => runtime.updateSettings({ startupAudio: !runtime.settings.startupAudio })} />
          <Toggle label="Launch Jarvis at login" checked={openAtLogin} onChange={toggleOpenAtLogin} />
        </SettingsCard>

        <SettingsCard icon={Brain} title="AI provider">
          <p className="mb-3 text-sm text-textSecondary">Switch the default provider instantly. Detailed keys, routes, and model settings are below.</p>
          <div className="grid grid-cols-2 gap-2">
            {providers.map((provider) => (
              <button
                key={provider}
                type="button"
                onClick={() => {
                  runtime.updateSettings({ aiProvider: provider });
                  patchProviderConfig({ active_provider: provider });
                }}
                className={`rounded-2xl border border-line px-3 py-2 text-sm capitalize ${
                  (runtime.aiProviderConfig?.active_provider || runtime.settings.aiProvider) === provider ? "bg-cyanCore/10 text-cyanCore" : "text-textSecondary hover:text-textPrimary"
                }`}
              >
                {provider}
              </button>
            ))}
          </div>
          <p className="mt-3 text-xs text-textSecondary">Ollama uses your local server at `http://127.0.0.1:11434` by default.</p>
        </SettingsCard>
      </div>

      <section className="panel rounded-[28px] p-5">
        <div className="mb-5 flex flex-wrap items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="rounded-2xl border border-cyanCore/20 bg-cyanCore/10 p-3 text-cyanCore">
              <Cloud size={22} />
            </div>
            <div>
              <h2 className="text-xl font-semibold tracking-[-0.03em] text-textPrimary">AI Providers</h2>
              <p className="mt-1 max-w-2xl text-sm leading-6 text-textSecondary">
                Connect cloud models, Ollama, llama.cpp, and local voice models. Keys stay encrypted in backend runtime storage and are never returned to the UI.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={refreshProviders}
            className="inline-flex h-10 items-center gap-2 rounded-2xl border border-line bg-white/[0.035] px-3 text-sm text-textSecondary hover:text-textPrimary"
          >
            <RefreshCcw size={16} />
            Refresh
          </button>
        </div>

        <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_360px]">
          <div className="grid gap-3 lg:grid-cols-2">
            {(runtime.aiProviders || []).map((provider) => (
              <ProviderCard
                key={provider.id}
                provider={provider}
                config={runtime.aiProviderConfig}
                apiKey={providerKeys[provider.id] || ""}
                visible={Boolean(visibleKeys[provider.id])}
                test={providerTests[provider.id]}
                onKeyChange={(value) => setProviderKeys((current) => ({ ...current, [provider.id]: value }))}
                onToggleVisible={() => setVisibleKeys((current) => ({ ...current, [provider.id]: !current[provider.id] }))}
                onSaveKey={() => saveKey(provider.id)}
                onRemoveKey={() => removeKey(provider.id)}
                onTest={() => runProviderTest(provider.id, provider.model)}
                onEnable={() => patchProviderConfig({ enabled: { [provider.id]: !provider.enabled } })}
                onSelect={() => patchProviderConfig({ active_provider: provider.id })}
                onModelChange={(model) => patchProviderConfig({ models: { [provider.id]: model } })}
              />
            ))}
          </div>

          <aside className="space-y-4">
            <div className="rounded-[24px] border border-line bg-white/[0.025] p-4">
              <h3 className="text-base font-semibold text-textPrimary">Model routing</h3>
              <p className="mt-1 text-sm text-textSecondary">Choose which model class handles each task type.</p>
              <div className="mt-4 space-y-3">
                {["chat", "coding", "vision", "voice", "automation"].map((route) => (
                  <RouteSelect
                    key={route}
                    label={route}
                    value={runtime.aiProviderConfig?.routes?.[route] || "auto"}
                    providers={runtime.aiProviders || []}
                    onChange={(value) => patchProviderConfig({ routes: { [route]: value } })}
                  />
                ))}
              </div>
            </div>

            <div className="rounded-[24px] border border-line bg-white/[0.025] p-4">
              <h3 className="text-base font-semibold text-textPrimary">Model settings</h3>
              <RangeSetting
                label="Temperature"
                min={0}
                max={1}
                step={0.05}
                value={runtime.aiProviderConfig?.settings?.temperature ?? 0.72}
                onChange={(value) => patchProviderConfig({ settings: { temperature: Number(value) } })}
              />
              <NumberSetting
                label="Max tokens"
                value={runtime.aiProviderConfig?.settings?.max_tokens ?? 700}
                onChange={(value) => patchProviderConfig({ settings: { max_tokens: Number(value) } })}
              />
              <Toggle
                label="Offline mode"
                checked={Boolean(runtime.aiProviderConfig?.settings?.offline_mode)}
                onChange={() => patchProviderConfig({ settings: { offline_mode: !runtime.aiProviderConfig?.settings?.offline_mode } })}
              />
              <Toggle
                label="Hybrid failover"
                checked={Boolean(runtime.aiProviderConfig?.settings?.hybrid_mode ?? true)}
                onChange={() => patchProviderConfig({ settings: { hybrid_mode: !runtime.aiProviderConfig?.settings?.hybrid_mode } })}
              />
            </div>

            <div className="rounded-[24px] border border-line bg-white/[0.025] p-4">
              <div className="mb-3 flex items-center gap-2">
                <HardDrive size={17} className="text-cyanCore" />
                <h3 className="text-base font-semibold text-textPrimary">Ollama models</h3>
              </div>
              <div className="space-y-2">
                {(runtime.ollamaModels || []).slice(0, 8).map((model) => (
                  <button
                    key={model.name}
                    type="button"
                    onClick={() => patchProviderConfig({ models: { ollama: model.name } })}
                    className="w-full rounded-2xl border border-line bg-[#070B14]/45 p-3 text-left text-sm text-textSecondary hover:text-textPrimary"
                  >
                    {model.name}
                  </button>
                ))}
                {!(runtime.ollamaModels || []).length ? <p className="text-sm text-textSecondary">No Ollama models detected yet.</p> : null}
              </div>
            </div>
          </aside>
        </div>
      </section>

      <section className="panel rounded-[28px] p-5">
        <div className="mb-5 flex flex-wrap items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="rounded-2xl border border-cyanCore/20 bg-cyanCore/10 p-3 text-cyanCore">
              <BrainCircuit size={22} />
            </div>
            <div>
              <h2 className="text-xl font-semibold tracking-[-0.03em] text-textPrimary">Memory & Brain Storage</h2>
              <p className="mt-1 max-w-2xl text-sm leading-6 text-textSecondary">
                Jarvis stores conversations, workflows, projects, preferences, browser history, automation context, and backups locally.
              </p>
            </div>
          </div>
          <span className="rounded-full border border-line px-3 py-1.5 text-xs font-semibold text-textSecondary">
            {runtime.memoryStorage?.usage?.display || "0 B"}
          </span>
        </div>

        <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_360px]">
          <div className="rounded-[24px] border border-line bg-white/[0.025] p-4">
            <label className="text-sm font-medium text-textPrimary" htmlFor="memory-folder">Current memory location</label>
            <div className="mt-3 flex gap-2">
              <input
                id="memory-folder"
                value={memoryPath}
                onChange={(event) => setMemoryPath(event.target.value)}
                placeholder="~/Desktop/Jarvis Brain"
                className="min-w-0 flex-1 rounded-2xl border border-line bg-[#070B14]/70 px-3 py-2 text-sm text-textPrimary outline-none"
              />
              <button type="button" onClick={chooseMemoryFolder} className="rounded-2xl border border-line px-3 text-sm text-textSecondary hover:text-textPrimary">
                Browse
              </button>
              <button type="button" onClick={saveMemoryFolder} className="rounded-2xl bg-cyanCore px-3 text-sm font-semibold text-[#021018]">
                Save
              </button>
            </div>

            <div className="mt-5 grid gap-2 sm:grid-cols-2">
              {(runtime.memoryStorage?.structure || ["conversations", "workflows", "projects", "preferences", "voice", "browser", "automation", "cache", "embeddings", "logs"]).map((name) => (
                <div key={name} className="rounded-2xl border border-line bg-[#070B14]/45 px-3 py-2 text-sm text-textSecondary">
                  {name}
                </div>
              ))}
            </div>
          </div>

          <aside className="rounded-[24px] border border-line bg-white/[0.025] p-4">
            <h3 className="text-base font-semibold text-textPrimary">Brain Controls</h3>
            <p className="mt-2 text-sm text-textSecondary">
              {runtime.memoryStorage?.usage?.files || 0} file(s), {runtime.memoryStorage?.initialized ? "database ready" : "not initialized"}
            </p>
            <div className="mt-4 grid gap-2">
              <button type="button" onClick={backupBrain} className="inline-flex h-11 items-center justify-center gap-2 rounded-2xl border border-line text-sm text-textSecondary hover:text-textPrimary">
                <Download size={16} />
                Backup memory
              </button>
              <button type="button" onClick={clearBrain} className="inline-flex h-11 items-center justify-center gap-2 rounded-2xl border border-red-400/20 text-sm text-red-200 hover:bg-red-400/10">
                <Trash2 size={16} />
                Clear brain storage
              </button>
            </div>
            <div className="mt-4 space-y-2">
              {(runtime.memoryStorage?.recent || []).slice(0, 4).map((item) => (
                <div key={item.id} className="rounded-2xl border border-line bg-[#070B14]/45 p-3">
                  <p className="truncate text-sm text-textPrimary">{item.title}</p>
                  <p className="mt-1 text-xs capitalize text-textSecondary">{item.kind}</p>
                </div>
              ))}
            </div>
          </aside>
        </div>
      </section>

      <section className="panel rounded-[28px] p-5">
        <div className="mb-5 flex flex-wrap items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="rounded-2xl border border-cyanCore/20 bg-cyanCore/10 p-3 text-cyanCore">
              <ShieldCheck size={22} />
            </div>
            <div>
              <h2 className="text-xl font-semibold tracking-[-0.03em] text-textPrimary">Security & Permissions</h2>
              <p className="mt-1 max-w-2xl text-sm leading-6 text-textSecondary">
                Control Jarvis access to apps, files, automation, memory, and background voice behavior.
              </p>
            </div>
          </div>
          <span className={`rounded-full border px-3 py-1.5 text-xs font-semibold ${saving ? "border-amber-300/30 text-amber-200" : "border-emerald-300/20 text-emerald-200"}`}>
            {saving ? "Saving" : permissions.safeMode ? "Safe Mode" : permissions.fullSystemAccess ? "Full Access" : "Controlled"}
          </span>
        </div>

        <div className="grid gap-3 lg:grid-cols-3">
          <PermissionMode
            icon={LockKeyhole}
            title="Allow Full System Access"
            text="Enables trusted automation while protected folders, files, and apps stay blocked."
            checked={permissions.fullSystemAccess}
            onChange={() => patchPermissions({ fullSystemAccess: !permissions.fullSystemAccess })}
          />
          <PermissionMode
            icon={ShieldCheck}
            title="Safe Mode"
            text="Jarvis asks before every action and avoids automatic execution."
            checked={permissions.safeMode}
            onChange={() => patchPermissions({ safeMode: !permissions.safeMode })}
          />
          <PermissionMode
            icon={Zap}
            title="Auto Execution Mode"
            text="Trusted low-risk actions can run automatically when allowed."
            checked={permissions.autoExecutionMode}
            onChange={() => patchPermissions({ autoExecutionMode: !permissions.autoExecutionMode })}
          />
        </div>

        <div className="mt-5 grid gap-4 xl:grid-cols-[minmax(0,1.2fr)_minmax(360px,0.8fr)]">
          <div className="space-y-4">
            <div className="rounded-[24px] border border-line bg-white/[0.025] p-4">
              <h3 className="mb-3 text-base font-semibold text-textPrimary">Access Control</h3>
              <div className="grid gap-2 md:grid-cols-2">
                {accessControls.map(([key, label, Icon]) => (
                  <Toggle
                    key={key}
                    icon={Icon}
                    label={label}
                    checked={Boolean(permissions.controls?.[key])}
                    onChange={() => patchPermissions({ controls: { [key]: !permissions.controls?.[key] } })}
                  />
                ))}
              </div>
            </div>

            <div className="grid gap-4 lg:grid-cols-3">
              <ListEditor
                icon={FolderLock}
                title="Protected Folders"
                placeholder="C:\\Users\\You\\Documents\\Passwords"
                items={permissions.protectedFolders || []}
                onChange={(items) => patchPermissions({ protectedFolders: items })}
              />
              <ListEditor
                icon={LockKeyhole}
                title="Protected Files"
                placeholder="C:\\path\\private.xlsx"
                items={permissions.protectedFiles || []}
                onChange={(items) => patchPermissions({ protectedFiles: items })}
              />
              <ListEditor
                icon={AppWindow}
                title="Protected Apps"
                placeholder="Bitwarden"
                items={permissions.protectedApps || []}
                onChange={(items) => patchPermissions({ protectedApps: items })}
              />
            </div>

            <ListEditor
              icon={FolderCheck}
              title="Allowed Workspaces"
              placeholder="D:\\Projects"
              items={permissions.allowedWorkspaces || []}
              onChange={(items) => patchPermissions({ allowedWorkspaces: items })}
              wide
            />
          </div>

          <aside className="space-y-4">
            <div className="rounded-[24px] border border-line bg-white/[0.025] p-4">
              <h3 className="mb-3 text-base font-semibold text-textPrimary">Confirmation Levels</h3>
              <RiskToggle label="Low risk" detail="Open apps, read folders, search files" checked={permissions.confirmations?.low} onChange={() => patchPermissions({ confirmations: { low: !permissions.confirmations?.low } })} />
              <RiskToggle label="Medium risk" detail="Create files, edit code, browser automation" checked={permissions.confirmations?.medium} onChange={() => patchPermissions({ confirmations: { medium: !permissions.confirmations?.medium } })} />
              <RiskToggle label="High risk" detail="Delete files, terminal commands, system changes" checked={permissions.confirmations?.high} onChange={() => patchPermissions({ confirmations: { high: !permissions.confirmations?.high } })} />
            </div>

            <div className="rounded-[24px] border border-line bg-white/[0.025] p-4">
              <div className="mb-3 flex items-center gap-2">
                <DatabaseZap size={17} className="text-cyanCore" />
                <h3 className="text-base font-semibold text-textPrimary">Memory Privacy</h3>
              </div>
              <Toggle label="Allow memory" checked={permissions.memoryEnabled} onChange={() => patchPermissions({ memoryEnabled: !permissions.memoryEnabled })} />
              <div className="mt-3 grid grid-cols-2 gap-2">
                <button type="button" onClick={handleExportMemory} className="inline-flex h-11 items-center justify-center gap-2 rounded-2xl border border-line text-sm text-textSecondary hover:text-textPrimary">
                  <Download size={16} />
                  Export
                </button>
                <button type="button" onClick={handleClearMemory} className="inline-flex h-11 items-center justify-center gap-2 rounded-2xl border border-red-400/20 text-sm text-red-200 hover:bg-red-400/10">
                  <Trash2 size={16} />
                  Clear
                </button>
              </div>
              <p className="mt-3 text-sm text-textSecondary">Saved memory items: {runtime.memory?.memory_count || 0}</p>
            </div>

            <div className="rounded-[24px] border border-line bg-white/[0.025] p-4">
              <div className="mb-3 flex items-center gap-2">
                <Activity size={17} className="text-cyanCore" />
                <h3 className="text-base font-semibold text-textPrimary">Live Action Monitor</h3>
              </div>
              <div className="max-h-[340px] space-y-2 overflow-auto pr-1">
                {(runtime.permissionActivity.length ? runtime.permissionActivity : runtime.executionLogs).slice(0, 14).map((item) => (
                  <div key={item.id} className="rounded-2xl border border-line bg-[#070B14]/45 p-3">
                    <div className="flex items-center justify-between gap-2">
                      <span className={`text-xs font-semibold capitalize ${item.level === "error" ? "text-red-200" : item.level === "warning" ? "text-amber-200" : "text-cyanCore"}`}>
                        {item.level || "info"}
                      </span>
                      <span className="text-[11px] text-textSecondary">{new Date(item.createdAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
                    </div>
                    <p className="mt-1 text-sm text-textPrimary">{item.message}</p>
                  </div>
                ))}
              </div>
            </div>
          </aside>
        </div>
      </section>

      <SettingsCard icon={KeyRound} title="Environment keys">
        <p className="text-sm leading-6 text-textSecondary">
          API keys stay in `.env`. This page controls what Jarvis may do with the system once a model decides on an action.
        </p>
      </SettingsCard>

      <SettingsCard icon={Linkedin} title="About JX Jarvis">
        <p className="text-sm leading-6 text-textSecondary">
          Created by <span className="font-medium text-textPrimary">Jojin John</span>. Follow the project creator on LinkedIn for updates and releases.
        </p>
        <a
          href="https://www.linkedin.com/in/jojin-john-74386b34a"
          target="_blank"
          rel="noreferrer"
          className="mt-4 inline-flex h-11 items-center justify-center rounded-2xl border border-line bg-white/[0.035] px-4 text-sm font-medium text-textPrimary transition hover:border-cyanCore/40 hover:text-cyanCore"
        >
          Open LinkedIn
        </a>
      </SettingsCard>
    </div>
  );
}

function SettingsCard({ icon: Icon, title, children }) {
  return (
    <section className="panel rounded-[28px] p-5">
      <div className="mb-4 flex items-center gap-2">
        <Icon size={17} className="text-cyanCore" />
        <h2 className="text-base font-semibold text-textPrimary">{title}</h2>
      </div>
      {children}
    </section>
  );
}

function ProviderCard({
  provider,
  config,
  apiKey,
  visible,
  test,
  onKeyChange,
  onToggleVisible,
  onSaveKey,
  onRemoveKey,
  onTest,
  onEnable,
  onSelect,
  onModelChange,
}) {
  const active = config?.active_provider === provider.id;
  return (
    <div className={`rounded-[24px] border p-4 ${active ? "border-cyanCore/35 bg-cyanCore/10" : "border-line bg-white/[0.025]"}`}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="grid h-9 w-9 place-items-center rounded-2xl bg-white/[0.06] text-sm font-bold text-cyanCore">
              {provider.label.slice(0, 2).toUpperCase()}
            </span>
            <div>
              <h3 className="text-sm font-semibold text-textPrimary">{provider.label}</h3>
              <p className="text-xs capitalize text-textSecondary">{provider.kind} provider</p>
            </div>
          </div>
        </div>
        <span className={`rounded-full px-2 py-1 text-[11px] font-semibold ${provider.connected ? "bg-cyanCore/10 text-cyanCore" : "bg-white/[0.06] text-textSecondary"}`}>
          {provider.status}
        </span>
      </div>

      <div className="mt-4 grid gap-2">
        <label className="text-xs font-medium text-textSecondary" htmlFor={`${provider.id}-model`}>Current model</label>
        <input
          id={`${provider.id}-model`}
          value={provider.model || ""}
          onChange={(event) => onModelChange(event.target.value)}
          className="h-10 rounded-2xl border border-line bg-[#070B14]/70 px-3 text-sm text-textPrimary outline-none"
          placeholder="model id"
        />
      </div>

      {provider.requiresKey ? (
        <div className="mt-3">
          <label className="text-xs font-medium text-textSecondary" htmlFor={`${provider.id}-key`}>
            API key {provider.maskedKey ? `(${provider.maskedKey})` : ""}
          </label>
          <div className="mt-2 flex gap-2">
            <input
              id={`${provider.id}-key`}
              value={apiKey}
              onChange={(event) => onKeyChange(event.target.value)}
              type={visible ? "text" : "password"}
              className="min-w-0 flex-1 rounded-2xl border border-line bg-[#070B14]/70 px-3 py-2 text-sm text-textPrimary outline-none"
              placeholder="Paste new key"
            />
            <button type="button" onClick={onToggleVisible} className="grid h-10 w-10 place-items-center rounded-2xl border border-line text-textSecondary">
              {visible ? <EyeOff size={15} /> : <Eye size={15} />}
            </button>
          </div>
        </div>
      ) : null}

      <div className="mt-4 flex flex-wrap gap-2">
        <button type="button" onClick={onSelect} className="rounded-2xl border border-line px-3 py-2 text-sm text-textSecondary hover:text-textPrimary">
          Use
        </button>
        <button type="button" onClick={onEnable} className="rounded-2xl border border-line px-3 py-2 text-sm text-textSecondary hover:text-textPrimary">
          {provider.enabled ? "Disable" : "Enable"}
        </button>
        {provider.requiresKey ? (
          <>
            <button type="button" onClick={onSaveKey} className="rounded-2xl bg-cyanCore px-3 py-2 text-sm font-semibold text-[#021018]">
              Save key
            </button>
            {provider.configured ? (
              <button type="button" onClick={onRemoveKey} className="rounded-2xl border border-red-400/20 px-3 py-2 text-sm text-red-200">
                Remove
              </button>
            ) : null}
          </>
        ) : null}
        <button type="button" onClick={onTest} className="rounded-2xl border border-line px-3 py-2 text-sm text-textSecondary hover:text-textPrimary">
          Test
        </button>
      </div>

      {test ? (
        <p className={`mt-3 text-xs ${test.status === "error" ? "text-red-200" : test.status === "success" ? "text-cyanCore" : "text-textSecondary"}`}>
          {test.message}
        </p>
      ) : null}
    </div>
  );
}

function RouteSelect({ label, value, providers, onChange }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-medium capitalize text-textSecondary">{label}</span>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="h-10 w-full rounded-2xl border border-line bg-[#070B14]/70 px-3 text-sm text-textPrimary outline-none"
      >
        <option value="auto">Auto route</option>
        {providers.map((provider) => (
          <option key={provider.id} value={provider.id}>
            {provider.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function RangeSetting({ label, value, min, max, step, onChange }) {
  return (
    <label className="mb-3 block">
      <span className="mb-1 flex justify-between text-xs font-medium text-textSecondary">
        <span>{label}</span>
        <span>{value}</span>
      </span>
      <input type="range" min={min} max={max} step={step} value={value} onChange={(event) => onChange(event.target.value)} className="w-full accent-cyanCore" />
    </label>
  );
}

function NumberSetting({ label, value, onChange }) {
  return (
    <label className="mb-3 block">
      <span className="mb-1 block text-xs font-medium text-textSecondary">{label}</span>
      <input
        type="number"
        value={value}
        min={64}
        max={32000}
        onChange={(event) => onChange(event.target.value)}
        className="h-10 w-full rounded-2xl border border-line bg-[#070B14]/70 px-3 text-sm text-textPrimary outline-none"
      />
    </label>
  );
}

function PermissionMode({ icon: Icon, title, text, checked, onChange }) {
  return (
    <button
      type="button"
      onClick={onChange}
      className={`rounded-[24px] border p-4 text-left transition ${checked ? "border-cyanCore/40 bg-cyanCore/10" : "border-line bg-white/[0.025] hover:border-white/15"}`}
    >
      <div className="mb-4 flex items-center justify-between">
        <Icon size={20} className={checked ? "text-cyanCore" : "text-textSecondary"} />
        <Switch checked={checked} />
      </div>
      <h3 className="text-sm font-semibold text-textPrimary">{title}</h3>
      <p className="mt-2 text-sm leading-6 text-textSecondary">{text}</p>
    </button>
  );
}

function Toggle({ icon: Icon, label, checked, onChange }) {
  return (
    <button type="button" onClick={onChange} className="flex w-full items-center justify-between gap-3 rounded-2xl border border-line bg-white/[0.025] p-3">
      <span className="flex min-w-0 items-center gap-2 text-sm text-textPrimary">
        {Icon ? <Icon size={16} className="shrink-0 text-cyanCore" /> : null}
        <span className="truncate">{label}</span>
      </span>
      <Switch checked={checked} />
    </button>
  );
}

function Switch({ checked }) {
  return (
    <span className={`h-6 w-11 shrink-0 rounded-full p-1 transition ${checked ? "bg-cyanCore" : "bg-white/10"}`}>
      <span className={`block h-4 w-4 rounded-full bg-white transition ${checked ? "translate-x-5" : ""}`} />
    </span>
  );
}

function RiskToggle({ label, detail, checked, onChange }) {
  return (
    <button type="button" onClick={onChange} className="mb-2 flex w-full items-center justify-between gap-3 rounded-2xl border border-line bg-white/[0.025] p-3 text-left">
      <span>
        <span className="block text-sm font-medium text-textPrimary">{label}</span>
        <span className="block text-xs text-textSecondary">{detail}</span>
      </span>
      <Switch checked={checked} />
    </button>
  );
}

function ListEditor({ icon: Icon, title, placeholder, items, onChange, wide = false }) {
  const [value, setValue] = useState("");

  function addItem() {
    const next = value.trim();
    if (!next || items.includes(next)) return;
    onChange([...items, next]);
    setValue("");
  }

  return (
    <div className={`rounded-[24px] border border-line bg-white/[0.025] p-4 ${wide ? "lg:col-span-3" : ""}`}>
      <div className="mb-3 flex items-center gap-2">
        <Icon size={17} className="text-cyanCore" />
        <h3 className="text-base font-semibold text-textPrimary">{title}</h3>
      </div>
      <div className="flex gap-2">
        <input
          value={value}
          onChange={(event) => setValue(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") addItem();
          }}
          placeholder={placeholder}
          className="min-w-0 flex-1 rounded-2xl border border-line bg-[#070B14]/70 px-3 py-2 text-sm text-textPrimary outline-none placeholder:text-textSecondary"
        />
        <button type="button" onClick={addItem} className="grid h-10 w-10 shrink-0 place-items-center rounded-2xl bg-cyanCore text-[#021018]">
          <Plus size={17} />
        </button>
      </div>
      <div className="mt-3 space-y-2">
        {items.length ? (
          items.map((item) => (
            <div key={item} className="flex items-center justify-between gap-2 rounded-2xl border border-line bg-[#070B14]/45 px-3 py-2">
              <span className="min-w-0 truncate text-sm text-textSecondary">{item}</span>
              <button type="button" onClick={() => onChange(items.filter((entry) => entry !== item))} className="grid h-7 w-7 shrink-0 place-items-center rounded-xl text-textSecondary hover:bg-white/10 hover:text-textPrimary">
                <X size={14} />
              </button>
            </div>
          ))
        ) : (
          <p className="rounded-2xl border border-line bg-[#070B14]/45 p-3 text-sm text-textSecondary">No entries yet.</p>
        )}
      </div>
    </div>
  );
}
