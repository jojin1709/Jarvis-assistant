import { AnimatePresence, motion } from "framer-motion";
import { ArrowRight, Bot, BrainCircuit, Check, Database, FolderCheck, KeyRound, Mic2, Moon, ShieldCheck, Sparkles } from "lucide-react";
import { useMemo, useState } from "react";

import LogoMark from "../components/LogoMark.jsx";
import { completeOnboarding } from "../services/api.js";

const userTypes = ["Developer", "Student", "Creator", "Researcher", "Cybersecurity", "General Use"];
const themes = ["Dark", "Midnight", "Glass", "Light", "Graphite"];
const providers = ["Groq", "Sarvam", "DeepSeek", "Nvidia", "Ollama", "Auto"];

const initialSetup = {
  userName: "",
  userType: "Developer",
  voiceActivation: true,
  permissions: {
    fileSystemAccess: true,
    browserControl: true,
    appControl: true,
    terminalExecution: true,
    notifications: true,
    backgroundStartup: false,
  },
  workspacePaths: ["~/Desktop/Jarvis Workspace"],
  memoryPath: "~/Desktop/Jarvis Brain",
  memoryMode: "default",
  protectedFolders: ["~/Documents", "~/Pictures"],
  protectedApps: ["Bitwarden", "1Password", "Windows Security"],
  provider: "Groq",
  apiKey: "",
  theme: "Dark",
};

export default function OnboardingPage({ onComplete }) {
  const [step, setStep] = useState(0);
  const [setup, setSetup] = useState(initialSetup);
  const [saving, setSaving] = useState(false);
  const [entry, setEntry] = useState("");
  const [error, setError] = useState("");
  const totalSteps = 10;

  const canContinue = useMemo(() => {
    if (step === 0) return setup.userName.trim().length >= 2;
    return true;
  }, [setup.userName, step]);

  function patch(patchValue) {
    setSetup((current) => ({ ...current, ...patchValue }));
  }

  function togglePermission(key) {
    setSetup((current) => ({
      ...current,
      permissions: { ...current.permissions, [key]: !current.permissions[key] },
    }));
  }

  function addListItem(key) {
    const value = entry.trim();
    if (!value) return;
    setSetup((current) => ({
      ...current,
      [key]: current[key].includes(value) ? current[key] : [...current[key], value],
    }));
    setEntry("");
  }

  function removeListItem(key, item) {
    setSetup((current) => ({ ...current, [key]: current[key].filter((value) => value !== item) }));
  }

  async function chooseMemoryFolder() {
    const selected = await window.jxJarvis?.chooseFolder?.();
    if (selected) patch({ memoryPath: selected, memoryMode: "custom" });
  }

  async function finish() {
    setSaving(true);
    setError("");
    try {
      const permissions = {
        controls: {
          fileSystemAccess: setup.permissions.fileSystemAccess,
          browserControl: setup.permissions.browserControl,
          appControl: setup.permissions.appControl,
          terminalExecution: setup.permissions.terminalExecution,
          voiceActivation: setup.voiceActivation,
          backgroundListening: setup.voiceActivation,
          automationMode: true,
          internetAccess: setup.permissions.browserControl,
        },
        protectedFolders: setup.protectedFolders,
        protectedApps: setup.protectedApps,
        allowedWorkspaces: setup.workspacePaths,
      };

      const result = await completeOnboarding({
        profile: {
          user_name: setup.userName.trim(),
          user_type: setup.userType,
          voice_activation: setup.voiceActivation,
          manual_activation_only: !setup.voiceActivation,
          workspace_paths: setup.workspacePaths,
          memory_storage_path: setup.memoryPath,
          ai_provider: setup.provider.toLowerCase(),
          theme: setup.theme.toLowerCase(),
          preferences: { notifications: setup.permissions.notifications, backgroundStartup: setup.permissions.backgroundStartup },
        },
        permissions,
        memory: { path: setup.memoryPath },
        provider: { name: setup.provider.toLowerCase(), api_key: setup.apiKey },
      });
      onComplete(result.profile, result.permissions, setup);
    } catch (finishError) {
      setError(finishError.message || "Could not complete setup.");
    } finally {
      setSaving(false);
    }
  }

  function next() {
    if (!canContinue) return;
    if (step >= totalSteps - 1) finish();
    else setStep((value) => value + 1);
  }

  function back() {
    setStep((value) => Math.max(0, value - 1));
  }

  return (
    <main className="relative min-h-screen overflow-hidden bg-void text-textPrimary">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,rgba(0,229,255,.12),transparent_34%)]" />
      <div className="relative z-10 mx-auto grid min-h-screen w-full max-w-6xl place-items-center px-4 py-8">
        <section className="app-surface grid w-full overflow-hidden rounded-[34px] lg:grid-cols-[0.85fr_1.15fr]">
          <aside className="border-b border-line p-8 lg:border-b-0 lg:border-r">
            <LogoMark className="h-14 w-14" rounded="rounded-2xl" />
            <h1 className="mt-8 text-4xl font-semibold tracking-[-0.06em] text-textPrimary">Hello.<br />I'm JX Jarvis.</h1>
            <p className="mt-4 text-sm leading-6 text-textSecondary">A personal AI workspace that can listen, plan, browse, automate, remember, and help you build.</p>
            <div className="mt-8 h-2 overflow-hidden rounded-full bg-white/10">
              <div className="h-full rounded-full bg-cyanCore transition-all duration-500" style={{ width: `${((step + 1) / totalSteps) * 100}%` }} />
            </div>
            <p className="mt-3 text-xs text-textSecondary">Step {step + 1} of {totalSteps}</p>
          </aside>

          <div className="p-6 sm:p-8">
            <AnimatePresence mode="wait">
              <motion.div
                key={step}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -12 }}
                transition={{ duration: 0.22 }}
                className="min-h-[520px]"
              >
                {step === 0 && (
                  <SetupBlock icon={Bot} title="What should I call you?" text="This name is used for greetings, memory, and voice responses.">
                    <input
                      autoFocus
                      value={setup.userName}
                      onChange={(event) => patch({ userName: event.target.value })}
                      placeholder="Your name"
                      className="mt-6 w-full rounded-3xl border border-line bg-[#070B14]/70 px-5 py-4 text-lg text-textPrimary outline-none placeholder:text-textSecondary"
                    />
                  </SetupBlock>
                )}

                {step === 1 && (
                  <SetupBlock icon={Sparkles} title="How would you like to use Jarvis?" text="Jarvis will tune suggestions, workflows, and quick actions around this.">
                    <OptionGrid items={userTypes} selected={setup.userType} onSelect={(userType) => patch({ userType })} />
                  </SetupBlock>
                )}

                {step === 2 && (
                  <SetupBlock icon={Mic2} title="Enable voice activation?" text="Use Hey Jarvis for hands-free activation, or keep voice manual.">
                    <ChoiceCard title='Enable "Hey Jarvis"' text="Background listening stays local and follows your permission settings." checked={setup.voiceActivation} onClick={() => patch({ voiceActivation: true })} />
                    <ChoiceCard title="Manual activation only" text="Use the Voice page or command controls when you want Jarvis to listen." checked={!setup.voiceActivation} onClick={() => patch({ voiceActivation: false })} />
                  </SetupBlock>
                )}

                {step === 3 && (
                  <SetupBlock icon={ShieldCheck} title="Choose permissions" text="You can change all of this later in Settings -> Security & Permissions.">
                    <PermissionToggle label="File System Access" text="Create, edit, organize, and search files in allowed workspaces." checked={setup.permissions.fileSystemAccess} onClick={() => togglePermission("fileSystemAccess")} />
                    <PermissionToggle label="Browser Automation" text="Open a visible browser, type, click, scroll, and summarize pages." checked={setup.permissions.browserControl} onClick={() => togglePermission("browserControl")} />
                    <PermissionToggle label="Desktop App Control" text="Open and close mapped apps like VS Code, Chrome, Terminal, Notepad." checked={setup.permissions.appControl} onClick={() => togglePermission("appControl")} />
                    <PermissionToggle label="Terminal Commands" text="Run approved terminal diagnostics and developer commands." checked={setup.permissions.terminalExecution} onClick={() => togglePermission("terminalExecution")} />
                    <PermissionToggle label="Notifications" text="Let Jarvis show native desktop status notifications." checked={setup.permissions.notifications} onClick={() => togglePermission("notifications")} />
                    <PermissionToggle label="Background Startup" text="Start Jarvis when Windows starts." checked={setup.permissions.backgroundStartup} onClick={() => togglePermission("backgroundStartup")} />
                  </SetupBlock>
                )}

                {step === 4 && (
                  <SetupBlock icon={FolderCheck} title="Where should Jarvis work?" text="Jarvis can freely create and organize files inside these safe workspaces.">
                    <ListEditor items={setup.workspacePaths} placeholder="D:\\Projects" onAdd={() => addListItem("workspacePaths")} onRemove={(item) => removeListItem("workspacePaths", item)} entry={entry} setEntry={setEntry} />
                  </SetupBlock>
                )}

                {step === 5 && (
                  <SetupBlock icon={BrainCircuit} title="Jarvis Memory Storage Setup" text="Jarvis uses local memory storage to remember conversations, workflows, projects, preferences, and AI context between sessions.">
                    <div className="grid gap-3 sm:grid-cols-3">
                      <ChoiceCard title="Use default" text="Desktop/Jarvis Brain" checked={setup.memoryMode === "default"} onClick={() => patch({ memoryMode: "default", memoryPath: "~/Desktop/Jarvis Brain" })} />
                      <ChoiceCard title="Create workspace" text="Use your Jarvis Workspace folder for brain data." checked={setup.memoryMode === "workspace"} onClick={() => patch({ memoryMode: "workspace", memoryPath: "~/Desktop/Jarvis Workspace/JarvisMemory" })} />
                      <ChoiceCard title="Custom folder" text="Pick a drive or folder you control." checked={setup.memoryMode === "custom"} onClick={chooseMemoryFolder} />
                    </div>
                    <div className="mt-5 rounded-3xl border border-line bg-white/[0.025] p-4">
                      <label className="text-sm text-textSecondary" htmlFor="memory-path">Memory location</label>
                      <input
                        id="memory-path"
                        value={setup.memoryPath}
                        onChange={(event) => patch({ memoryPath: event.target.value, memoryMode: "custom" })}
                        className="mt-2 w-full rounded-2xl border border-line bg-[#070B14]/70 px-4 py-3 text-sm text-textPrimary outline-none"
                      />
                      <div className="mt-4 grid gap-2 sm:grid-cols-2">
                        {["conversations", "workflows", "projects", "preferences", "voice", "browser", "automation", "cache", "embeddings", "logs"].map((name) => (
                          <div key={name} className="flex items-center gap-2 rounded-2xl border border-line bg-[#070B14]/45 px-3 py-2 text-sm text-textSecondary">
                            <Database size={14} className="text-cyanCore" />
                            {name}
                          </div>
                        ))}
                      </div>
                    </div>
                  </SetupBlock>
                )}

                {step === 6 && (
                  <SetupBlock icon={ShieldCheck} title="Protect sensitive areas" text="Jarvis will never access protected folders or control protected apps.">
                    <p className="mb-2 text-sm font-medium text-textPrimary">Protected folders</p>
                    <ListEditor items={setup.protectedFolders} placeholder="C:\\Sensitive Folder" onAdd={() => addListItem("protectedFolders")} onRemove={(item) => removeListItem("protectedFolders", item)} entry={entry} setEntry={setEntry} />
                    <p className="mb-2 mt-5 text-sm font-medium text-textPrimary">Protected apps</p>
                    <ListEditor items={setup.protectedApps} placeholder="Password Manager" onAdd={() => addListItem("protectedApps")} onRemove={(item) => removeListItem("protectedApps", item)} entry={entry} setEntry={setEntry} />
                  </SetupBlock>
                )}

                {step === 7 && (
                  <SetupBlock icon={KeyRound} title="Choose your AI provider" text="You can add or rotate keys later. Keys are stored only in local runtime storage.">
                    <OptionGrid items={providers} selected={setup.provider} onSelect={(provider) => patch({ provider })} />
                    <input
                      value={setup.apiKey}
                      onChange={(event) => patch({ apiKey: event.target.value })}
                      placeholder={`${setup.provider} API key (optional)`}
                      type="password"
                      className="mt-5 w-full rounded-3xl border border-line bg-[#070B14]/70 px-5 py-4 text-textPrimary outline-none placeholder:text-textSecondary"
                    />
                  </SetupBlock>
                )}

                {step === 8 && (
                  <SetupBlock icon={Moon} title="Pick a theme" text="The desktop can stay focused and calm, or a little more glassy.">
                    <OptionGrid items={themes} selected={setup.theme} onSelect={(theme) => patch({ theme })} />
                  </SetupBlock>
                )}

                {step === 9 && (
                  <SetupBlock icon={Check} title="Setup complete" text={`Welcome, ${setup.userName || "there"}. JX Jarvis is ready.`}>
                    <div className="mt-6 grid gap-3">
                      <Tip text='Try saying: "Hey Jarvis, open Chrome"' />
                      <Tip text='Try: "Create a modern portfolio website"' />
                      <Tip text='Try: "Search Google for AI news"' />
                    </div>
                    {error ? <p className="mt-5 rounded-2xl border border-red-400/20 bg-red-400/10 p-3 text-sm text-red-100">{error}</p> : null}
                  </SetupBlock>
                )}
              </motion.div>
            </AnimatePresence>

            <div className="mt-6 flex items-center justify-between gap-3">
              <button type="button" onClick={back} disabled={step === 0 || saving} className="rounded-2xl border border-line px-4 py-3 text-sm text-textSecondary transition hover:text-textPrimary disabled:opacity-40">
                Back
              </button>
              <button
                type="button"
                onClick={next}
                disabled={!canContinue || saving}
                className="inline-flex items-center gap-2 rounded-2xl bg-cyanCore px-5 py-3 text-sm font-semibold text-[#021018] transition disabled:opacity-40"
              >
                {step >= totalSteps - 1 ? (saving ? "Saving..." : "Open Jarvis") : "Continue"}
                <ArrowRight size={16} />
              </button>
            </div>
          </div>
        </section>
      </div>
    </main>
  );
}

function SetupBlock({ icon: Icon, title, text, children }) {
  return (
    <div>
      <div className="grid h-12 w-12 place-items-center rounded-2xl border border-cyanCore/20 bg-cyanCore/10 text-cyanCore">
        <Icon size={22} />
      </div>
      <h2 className="mt-6 text-3xl font-semibold tracking-[-0.05em] text-textPrimary">{title}</h2>
      <p className="mt-3 max-w-xl text-sm leading-6 text-textSecondary">{text}</p>
      <div className="mt-6">{children}</div>
    </div>
  );
}

function OptionGrid({ items, selected, onSelect }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {items.map((item) => (
        <button
          key={item}
          type="button"
          onClick={() => onSelect(item)}
          className={`rounded-3xl border p-4 text-left text-sm font-medium transition ${
            selected === item ? "border-cyanCore/45 bg-cyanCore/10 text-cyanCore" : "border-line bg-white/[0.025] text-textSecondary hover:text-textPrimary"
          }`}
        >
          {item}
        </button>
      ))}
    </div>
  );
}

function ChoiceCard({ title, text, checked, onClick }) {
  return (
    <button type="button" onClick={onClick} className={`mb-3 flex w-full gap-4 rounded-3xl border p-4 text-left transition ${checked ? "border-cyanCore/45 bg-cyanCore/10" : "border-line bg-white/[0.025]"}`}>
      <span className={`mt-1 grid h-6 w-6 shrink-0 place-items-center rounded-full border ${checked ? "border-cyanCore bg-cyanCore text-[#021018]" : "border-line text-transparent"}`}>
        <Check size={14} />
      </span>
      <span>
        <span className="block text-sm font-semibold text-textPrimary">{title}</span>
        <span className="mt-1 block text-sm leading-6 text-textSecondary">{text}</span>
      </span>
    </button>
  );
}

function PermissionToggle({ label, text, checked, onClick }) {
  return (
    <button type="button" onClick={onClick} className="mb-2 flex w-full items-center justify-between gap-4 rounded-2xl border border-line bg-white/[0.025] p-3 text-left">
      <span>
        <span className="block text-sm font-medium text-textPrimary">{label}</span>
        <span className="block text-xs text-textSecondary">{text}</span>
      </span>
      <span className={`h-6 w-11 shrink-0 rounded-full p-1 transition ${checked ? "bg-cyanCore" : "bg-white/10"}`}>
        <span className={`block h-4 w-4 rounded-full bg-white transition ${checked ? "translate-x-5" : ""}`} />
      </span>
    </button>
  );
}

function ListEditor({ items, placeholder, onAdd, onRemove, entry, setEntry }) {
  return (
    <div>
      <div className="flex gap-2">
        <input
          value={entry}
          onChange={(event) => setEntry(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") onAdd();
          }}
          placeholder={placeholder}
          className="min-w-0 flex-1 rounded-2xl border border-line bg-[#070B14]/70 px-4 py-3 text-sm text-textPrimary outline-none placeholder:text-textSecondary"
        />
        <button type="button" onClick={onAdd} className="rounded-2xl bg-cyanCore px-4 text-sm font-semibold text-[#021018]">
          Add
        </button>
      </div>
      <div className="mt-3 space-y-2">
        {items.map((item) => (
          <div key={item} className="flex items-center justify-between gap-2 rounded-2xl border border-line bg-white/[0.025] px-3 py-2">
            <span className="min-w-0 truncate text-sm text-textSecondary">{item}</span>
            <button type="button" onClick={() => onRemove(item)} className="text-sm text-textSecondary hover:text-textPrimary">Remove</button>
          </div>
        ))}
      </div>
    </div>
  );
}

function Tip({ text }) {
  return (
    <div className="rounded-2xl border border-line bg-white/[0.025] p-4 text-sm text-textSecondary">
      {text}
    </div>
  );
}
