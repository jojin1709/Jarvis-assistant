const { app, BrowserWindow, dialog, ipcMain, Menu } = require("electron");
const fs = require("node:fs");
const path = require("node:path");
const { spawn } = require("node:child_process");
const net = require("node:net");

const { createSplashWindow } = require("./splash");

const isPackaged = app.isPackaged;
const ROOT_DIR = isPackaged ? process.resourcesPath : path.join(__dirname, "..");
const APP_DIR = isPackaged ? app.getAppPath() : ROOT_DIR;
const BACKEND_DIR = isPackaged ? path.join(process.resourcesPath, "backend") : path.join(ROOT_DIR, "backend");
const BACKEND_PORT = process.env.JX_JARVIS_BACKEND_PORT || "8765";
const ICON_PATH = isPackaged
  ? path.join(process.resourcesPath, "assets", "icon.ico")
  : path.join(ROOT_DIR, "assets", "icon.ico");

let mainWindow;
let splashWindow;
let backendProcess;

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

async function createWindow() {
  splashWindow = createSplashWindow();
  await startBackend();

  mainWindow = new BrowserWindow({
    width: 1440,
    height: 920,
    minWidth: 1080,
    minHeight: 720,
    backgroundColor: "#02040a",
    title: "JX JARVIS",
    icon: ICON_PATH,
    frame: false,
    titleBarStyle: "hidden",
    show: false,
    opacity: 0,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      preload: path.join(__dirname, "preload.js"),
    },
  });

  mainWindow.setMenuBarVisibility(false);
  Menu.setApplicationMenu(null);

  mainWindow.on("maximize", () => mainWindow.webContents.send("window:state", { maximized: true }));
  mainWindow.on("unmaximize", () => mainWindow.webContents.send("window:state", { maximized: false }));

  mainWindow.once("ready-to-show", () => {
    setTimeout(() => {
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
    }, 900);
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
ipcMain.on("window:close", () => mainWindow?.close());
ipcMain.handle("window:is-maximized", () => Boolean(mainWindow?.isMaximized()));

if (gotSingleInstanceLock) {
  app.whenReady().then(createWindow);
}

app.on("second-instance", () => {
  if (!mainWindow) return;
  if (mainWindow.isMinimized()) mainWindow.restore();
  mainWindow.focus();
});

app.on("window-all-closed", () => {
  if (backendProcess && !backendProcess.killed) backendProcess.kill();
  if (process.platform !== "darwin") app.quit();
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});
