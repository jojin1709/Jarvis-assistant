const { app, BrowserWindow, Tray, dialog, globalShortcut, ipcMain, Menu, Notification, shell } = require("electron");
const fs = require("node:fs");
const path = require("node:path");
const { spawn } = require("node:child_process");
const net = require("node:net");

const { createSplashWindow, fadeOutSplash, waitForStartupAudio } = require("./splash");

const isPackaged = app.isPackaged;
const ROOT_DIR = isPackaged ? process.resourcesPath : path.join(__dirname, "..");
const APP_DIR = isPackaged ? app.getAppPath() : ROOT_DIR;
const BACKEND_DIR = isPackaged ? path.join(process.resourcesPath, "backend") : path.join(ROOT_DIR, "backend");
const BACKEND_PORT = process.env.JX_JARVIS_BACKEND_PORT || "8765";
const ICON_PATH = (() => {
  const root = isPackaged ? process.resourcesPath : ROOT_DIR;
  const preferred = path.join(root, "assets", "jx-jarvis.ico");
  const fallback = path.join(root, "assets", "icon.ico");
  return fs.existsSync(preferred) ? preferred : fallback;
})();

let mainWindow;
let splashWindow;
let backendProcess;
let tray;
let isQuitting = false;
let voiceEnabled = true;
let voiceMuted = false;
let voiceMode = "push_to_talk";
let voiceInFlight = false;

app.commandLine.appendSwitch("autoplay-policy", "no-user-gesture-required");
app.setAppUserModelId("com.jx.jarvis");

const gotSingleInstanceLock = app.requestSingleInstanceLock();

if (!gotSingleInstanceLock) {
  app.quit();
}

function assetPath(...parts) {
  return isPackaged ? path.join(process.resourcesPath, ...parts) : path.join(ROOT_DIR, ...parts);
}

function loadDotEnv() {
  const envPaths = isPackaged
    ? [path.join(app.getPath("userData"), ".env"), path.join(process.resourcesPath, ".env")]
    : [path.join(ROOT_DIR, ".env")];

  return envPaths
    .filter((envPath) => fs.existsSync(envPath))
    .flatMap((envPath) => fs.readFileSync(envPath, "utf8").split(/\r?\n/))
    .map((line) => line.trim())
    .filter((line) => line && !line.startsWith("#") && line.includes("="))
    .reduce((env, line) => {
      const index = line.indexOf("=");
      const key = line.slice(0, index).trim();
      const value = line.slice(index + 1).trim().replace(/^["']|["']$/g, "");
      env[key] = value;
      return env;
    }, {});
}

function portIsOpen(port) {
  return new Promise((resolve) => {
    const socket = net.createConnection({ host: "127.0.0.1", port: Number(port) });
    socket.on("connect", () => {
      socket.end();
      resolve(true);
    });
    socket.on("error", () => resolve(false));
    socket.setTimeout(500, () => {
      socket.destroy();
      resolve(false);
    });
  });
}

function backendCommand() {
  const packagedBackendExe = path.join(process.resourcesPath, "backend-dist", "jx-jarvis-backend.exe");
  const venvPython = path.join(BACKEND_DIR, ".venv", "Scripts", "python.exe");
  const fallbackVenvPython = path.join(BACKEND_DIR, "venv", "Scripts", "python.exe");

  if (isPackaged && fs.existsSync(packagedBackendExe)) {
    return { command: packagedBackendExe, args: [], packagedExe: true };
  }

  if (process.platform === "win32") {
    if (fs.existsSync(venvPython)) return { command: venvPython, args: [], packagedExe: false };
    if (fs.existsSync(fallbackVenvPython)) return { command: fallbackVenvPython, args: [], packagedExe: false };
    return { command: "py", args: ["-3"], packagedExe: false };
  }

  return { command: "python3", args: [], packagedExe: false };
}

async function startBackend() {
  if (await portIsOpen(BACKEND_PORT)) return;

  const python = backendCommand();
  const backendEnv = loadDotEnv();
  backendProcess = spawn(
    python.command,
    python.packagedExe
      ? []
      : [
          ...python.args,
          "-m",
          "app.main",
        ],
    {
      cwd: python.packagedExe ? path.dirname(python.command) : BACKEND_DIR,
      env: { ...process.env, ...backendEnv, PYTHONUNBUFFERED: "1", JX_JARVIS_PACKAGED: isPackaged ? "true" : "false" },
      stdio: "pipe",
      windowsHide: true,
    },
  );

  backendProcess.stderr.on("data", (data) => console.error(`[JX Backend] ${data}`));
  backendProcess.stdout.on("data", (data) => console.log(`[JX Backend] ${data}`));
  backendProcess.on("error", (error) => {
    dialog.showErrorBox("JX JARVIS backend failed", error.message);
  });
}

function stopBackendProcess() {
  if (!backendProcess || backendProcess.killed) return;

  const backend = backendProcess;
  const backendPid = backendProcess.pid;
  if (process.platform === "win32" && backendPid) {
    const taskkill = spawn("taskkill", ["/pid", String(backendPid), "/T", "/F"], {
      stdio: "ignore",
      windowsHide: true,
    });
    taskkill.on("error", () => backend.kill());
  } else {
    backend.kill();
  }

  backendProcess = undefined;
}

function quitJarvis() {
  if (isQuitting) return;
  isQuitting = true;
  stopBackendProcess();
  app.quit();
}

function showMainWindow() {
  if (!mainWindow) return;
  if (mainWindow.isMinimized()) mainWindow.restore();
  mainWindow.show();
  mainWindow.focus();
}

function sendGlobalCommand(command) {
  showMainWindow();
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.webContents.send("global:command", command);
  }
}

function notify(title, body) {
  if (!Notification.isSupported()) return;
  new Notification({ title, body, icon: ICON_PATH }).show();
}

function emitVoiceEvent(event) {
  if (mainWindow && !mainWindow.isDestroyed()) {
    mainWindow.webContents.send("voice:event", event);
  }
}

async function backendRequest(pathname, options = {}) {
  const response = await fetch(`http://127.0.0.1:${BACKEND_PORT}${pathname}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const text = await response.text();
  let payload = {};
  try {
    payload = text ? JSON.parse(text) : {};
  } catch {
    payload = { response: text };
  }
  if (!response.ok) {
    throw new Error(payload.error || payload.response || `Backend request failed with ${response.status}`);
  }
  return payload;
}

async function setVoiceRuntime(patch) {
  const result = await backendRequest("/api/voice/runtime", {
    method: "PATCH",
    body: JSON.stringify(patch),
  });
  const runtime = result.runtime || {};
  voiceEnabled = runtime.enabled !== false;
  voiceMuted = Boolean(runtime.muted);
  voiceMode = runtime.mode || voiceMode;
  updateTrayMenu();
  emitVoiceEvent({ type: "runtime", runtime });
  return runtime;
}

async function triggerPushToTalk(source = "global_hotkey") {
  if (!voiceEnabled || voiceInFlight) return;
  voiceInFlight = true;
  emitVoiceEvent({ type: "activation", source, hotkey: "Space+M" });
  try {
    const result = await backendRequest("/api/voice/push-to-talk", {
      method: "POST",
      body: JSON.stringify({ source, speak: !voiceMuted }),
    });
    emitVoiceEvent({ type: "complete", source, result });
    if (result?.transcript) notify("JX JARVIS heard you", result.transcript);
  } catch (error) {
    emitVoiceEvent({ type: "error", source, message: error.message });
    notify("JX JARVIS voice failed", error.message);
  } finally {
    voiceInFlight = false;
  }
}

function updateTrayMenu() {
  if (!tray) return;
  tray.setToolTip(`JX JARVIS - voice ${voiceEnabled ? voiceMode.replaceAll("_", " ") : "disabled"}`);
  tray.setContextMenu(buildTrayMenu());
}

function buildTrayMenu() {
  return Menu.buildFromTemplate([
    { label: "Show JX JARVIS", click: showMainWindow },
    { label: "Assistant Overlay", click: () => sendGlobalCommand("assistant-overlay") },
    { label: "Command Palette", click: () => sendGlobalCommand("command-palette") },
    { label: "Hide to tray", click: () => mainWindow?.hide() },
    { type: "separator" },
    {
      label: "Enable Voice",
      type: "checkbox",
      checked: voiceEnabled,
      click: (item) => setVoiceRuntime({ enabled: item.checked }).catch((error) => notify("Voice runtime", error.message)),
    },
    {
      label: "Mute Jarvis",
      type: "checkbox",
      checked: voiceMuted,
      click: (item) => setVoiceRuntime({ muted: item.checked }).catch((error) => notify("Voice runtime", error.message)),
    },
    { label: "Push-To-Talk Space+M", click: () => triggerPushToTalk("tray") },
    {
      label: "Continuous Listening",
      type: "radio",
      checked: voiceMode === "continuous",
      click: () => setVoiceRuntime({ mode: "continuous" }).catch((error) => notify("Voice runtime", error.message)),
    },
    {
      label: "Push-To-Talk Mode",
      type: "radio",
      checked: voiceMode === "push_to_talk",
      click: () => setVoiceRuntime({ mode: "push_to_talk" }).catch((error) => notify("Voice runtime", error.message)),
    },
    { type: "separator" },
    {
      label: "Quit",
      click: quitJarvis,
    },
  ]);
}

function createTray() {
  if (tray || !fs.existsSync(ICON_PATH)) return;

  tray = new Tray(ICON_PATH);
  updateTrayMenu();
  tray.on("click", showMainWindow);
}

async function createWindow() {
  splashWindow = createSplashWindow();
  const startupAudioPromise = waitForStartupAudio(splashWindow);
  await startBackend();

  mainWindow = new BrowserWindow({
    width: 1440,
    height: 920,
    minWidth: 1080,
    minHeight: 720,
    backgroundColor: "#070B14",
    title: "JX JARVIS",
    icon: ICON_PATH,
    frame: false,
    titleBarStyle: "hidden",
    show: false,
    opacity: 0,
    webPreferences: {
      contextIsolation: true,
      backgroundThrottling: false,
      nodeIntegration: false,
      preload: path.join(__dirname, "preload.js"),
    },
  });

  mainWindow.setMenuBarVisibility(false);
  Menu.setApplicationMenu(null);

  mainWindow.on("maximize", () => mainWindow.webContents.send("window:state", { maximized: true }));
  mainWindow.on("unmaximize", () => mainWindow.webContents.send("window:state", { maximized: false }));
  mainWindow.on("close", (event) => {
    if (isQuitting) return;
    event.preventDefault();
    mainWindow.hide();
    notify("JX JARVIS is still running", "Voice hotkey Space+M remains active in the tray.");
  });

  mainWindow.once("ready-to-show", async () => {
    await startupAudioPromise;
    await fadeOutSplash(splashWindow);
    if (splashWindow && !splashWindow.isDestroyed()) splashWindow.close();
    mainWindow.show();
    let opacity = 0;
    const fade = setInterval(() => {
      opacity = Math.min(opacity + 0.08, 1);
      if (!mainWindow || mainWindow.isDestroyed()) {
        clearInterval(fade);
        return;
      }
      mainWindow.setOpacity(opacity);
      if (opacity >= 1) clearInterval(fade);
    }, 16);
  });

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (/^https?:\/\//i.test(url)) {
      shell.openExternal(url);
      return { action: "deny" };
    }
    return { action: "allow" };
  });

  mainWindow.webContents.on("will-navigate", (event, url) => {
    const currentUrl = mainWindow.webContents.getURL();
    if (/^https?:\/\//i.test(url) && url !== currentUrl && !url.startsWith(process.env.VITE_DEV_SERVER_URL || "file://")) {
      event.preventDefault();
      shell.openExternal(url);
    }
  });

  const devUrl = process.env.VITE_DEV_SERVER_URL;
  if (devUrl) {
    await mainWindow.loadURL(devUrl);
  } else {
    await mainWindow.loadFile(path.join(APP_DIR, "frontend", "dist", "index.html"));
  }
}

ipcMain.on("window:minimize", () => mainWindow?.minimize());
ipcMain.on("window:maximize", () => {
  if (!mainWindow) return;
  if (mainWindow.isMaximized()) mainWindow.unmaximize();
  else mainWindow.maximize();
});
ipcMain.on("window:close", () => {
  if (isQuitting) return;
  mainWindow?.hide();
});
ipcMain.handle("window:is-maximized", () => Boolean(mainWindow?.isMaximized()));
ipcMain.handle("system:get-open-at-login", () => app.getLoginItemSettings().openAtLogin);
ipcMain.handle("system:set-open-at-login", (_event, enabled) => {
  app.setLoginItemSettings({ openAtLogin: Boolean(enabled) });
  return app.getLoginItemSettings().openAtLogin;
});
ipcMain.handle("system:open-external", async (_event, url) => {
  const target = String(url || "");
  if (!/^https?:\/\//i.test(target)) return false;
  await shell.openExternal(target);
  return true;
});
ipcMain.handle("system:choose-folder", async (_event, title) => {
  const result = await dialog.showOpenDialog(mainWindow, {
    title: String(title || "Choose folder"),
    properties: ["openDirectory", "createDirectory"],
  });
  if (result.canceled || !result.filePaths.length) return null;
  return result.filePaths[0];
});
ipcMain.handle("voice:push-to-talk", () => triggerPushToTalk("renderer"));
ipcMain.handle("voice:set-runtime", (_event, patch) => setVoiceRuntime(patch || {}));

if (gotSingleInstanceLock) {
  app.whenReady().then(async () => {
    createTray();
    await createWindow();
    globalShortcut.register("CommandOrControl+K", () => sendGlobalCommand("command-palette"));
    globalShortcut.register("Alt+Space", () => sendGlobalCommand("assistant-overlay"));
    const pttRegistered = globalShortcut.register("Space+M", () => triggerPushToTalk("global_hotkey"));
    if (!pttRegistered) {
      const fallbackRegistered = globalShortcut.register("Alt+M", () => triggerPushToTalk("global_hotkey_fallback"));
      notify("JX JARVIS voice hotkey", fallbackRegistered ? "Space+M was unavailable, using Alt+M fallback." : "Voice hotkey registration failed.");
    }
    setVoiceRuntime({ enabled: true }).catch((error) => console.error(`[JX Voice] ${error.message}`));
    notify("JX JARVIS is running", "Voice runtime is ready. Press Space+M for push-to-talk.");
  });
}

app.on("second-instance", () => {
  showMainWindow();
});

app.on("window-all-closed", () => {
  if (isQuitting) stopBackendProcess();
  if (isQuitting && process.platform !== "darwin") app.quit();
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
  else showMainWindow();
});

app.on("before-quit", () => {
  isQuitting = true;
  globalShortcut.unregisterAll();
  stopBackendProcess();
});
