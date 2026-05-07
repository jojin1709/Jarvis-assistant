const { BrowserWindow } = require("electron");
const fs = require("node:fs");
const path = require("node:path");
const { pathToFileURL } = require("node:url");

function splashHtml() {
  const projectRoot = path.join(__dirname, "..");
  const resourceRoot =
    process.resourcesPath && fs.existsSync(path.join(process.resourcesPath, "assets"))
      ? process.resourcesPath
      : projectRoot;
  const soundCandidates = [
    { path: path.join(resourceRoot, "assets", "sounds", "startup.wav"), mime: "audio/wav" },
    { path: path.join(resourceRoot, "assets", "sounds", "startup.mp3"), mime: "audio/mpeg" },
  ];
  const startupSound = soundCandidates.find((sound) => fs.existsSync(sound.path));
  const soundSrc = startupSound ? pathToFileURL(startupSound.path).toString() : "";

  return `<!doctype html>
<html>
  <head>
    <meta charset="UTF-8" />
    <style>
      * { box-sizing: border-box; }
      body {
        margin: 0;
        width: 100vw;
        height: 100vh;
        overflow: hidden;
        background: #02040a;
        font-family: "Segoe UI", Arial, sans-serif;
        color: #dffcff;
      }
      .shell {
        position: relative;
        display: grid;
        place-items: center;
        width: 100vw;
        height: 100vh;
        border: 1px solid rgba(56, 246, 255, 0.45);
        background:
          radial-gradient(circle at 50% 44%, rgba(56,246,255,.2), transparent 24%),
          radial-gradient(circle at 70% 20%, rgba(168,85,247,.14), transparent 28%),
          linear-gradient(rgba(56,246,255,.05) 1px, transparent 1px),
          linear-gradient(90deg, rgba(56,246,255,.05) 1px, transparent 1px);
        background-size: auto, auto, 34px 34px, 34px 34px;
        box-shadow: inset 0 0 60px rgba(56,246,255,.15);
      }
      .orb {
        width: 168px;
        height: 168px;
        border-radius: 50%;
        border: 1px solid rgba(125,239,255,.9);
        background: radial-gradient(circle, rgba(223,252,255,.95) 0 11%, rgba(56,246,255,.22) 12% 39%, rgba(168,85,247,.12) 40% 100%);
        box-shadow: 0 0 50px rgba(56,246,255,.55), inset 0 0 38px rgba(56,246,255,.32);
        animation: pulse 1.45s ease-in-out infinite;
      }
      .ring, .ring2 {
        position: absolute;
        width: 240px;
        height: 240px;
        border: 1px solid rgba(56,246,255,.3);
        border-radius: 50%;
        animation: spin 4.2s linear infinite;
      }
      .ring2 {
        width: 306px;
        height: 306px;
        border-color: rgba(168,85,247,.25);
        animation-duration: 6.5s;
        animation-direction: reverse;
      }
      h1 {
        margin: 34px 0 8px;
        font-size: 34px;
        letter-spacing: 10px;
        font-weight: 700;
        text-shadow: 0 0 22px rgba(56,246,255,.55);
      }
      p {
        margin: 0;
        color: rgba(125,239,255,.75);
        font-size: 12px;
        letter-spacing: 5px;
      }
      .bar {
        width: 320px;
        height: 2px;
        margin-top: 26px;
        background: rgba(56,246,255,.15);
        overflow: hidden;
      }
      .bar::after {
        content: "";
        display: block;
        width: 42%;
        height: 100%;
        background: linear-gradient(90deg, transparent, #38f6ff, transparent);
        animation: boot 1.35s ease-in-out infinite;
      }
      @keyframes pulse {
        0%, 100% { transform: scale(.97); opacity: .82; }
        50% { transform: scale(1.04); opacity: 1; }
      }
      @keyframes spin { to { transform: rotate(360deg); } }
      @keyframes boot {
        from { transform: translateX(-100%); }
        to { transform: translateX(250%); }
      }
    </style>
  </head>
  <body>
    <div class="shell">
      <div>
        <div style="position:relative;display:grid;place-items:center;height:320px">
          <div class="ring"></div>
          <div class="ring2"></div>
          <div class="orb"></div>
        </div>
        <h1>JX JARVIS</h1>
        <p>BOOTING DESKTOP OPERATIONS CORE</p>
        <div class="bar"></div>
      </div>
    </div>
    ${
      soundSrc
        ? `<audio id="startup-audio" src="${soundSrc}" autoplay preload="auto"></audio>
    <script>
      const audio = document.getElementById("startup-audio");
      if (audio) {
        audio.volume = 0.9;
        audio.play().catch(() => {
          window.addEventListener("pointerdown", () => audio.play().catch(() => {}), { once: true });
          window.setTimeout(() => audio.play().catch(() => {}), 250);
          window.setTimeout(() => audio.play().catch(() => {}), 900);
        });
      }
    </script>`
        : ""
    }
  </body>
</html>`;
}

function createSplashWindow() {
  const projectRoot = path.join(__dirname, "..");
  const resourceRoot =
    process.resourcesPath && fs.existsSync(path.join(process.resourcesPath, "assets"))
      ? process.resourcesPath
      : projectRoot;
  const icon = path.join(resourceRoot, "assets", "icon.ico");
  const splash = new BrowserWindow({
    width: 620,
    height: 460,
    frame: false,
    transparent: false,
    resizable: false,
    show: false,
    backgroundColor: "#02040a",
    icon,
    webPreferences: {
      sandbox: true,
    },
  });

  splash.setMenuBarVisibility(false);
  splash.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(splashHtml())}`);
  splash.once("ready-to-show", () => splash.show());
  return splash;
}

async function waitForStartupAudio(splash, timeoutMs = 18000) {
  if (!splash || splash.isDestroyed()) return { played: false, reason: "splash missing" };

  try {
    if (splash.webContents.isLoadingMainFrame()) {
      await new Promise((resolve) => {
        splash.webContents.once("did-finish-load", resolve);
        splash.webContents.once("did-fail-load", resolve);
      });
    }
    if (splash.isDestroyed()) return { played: false, reason: "splash closed" };

    return await splash.webContents.executeJavaScript(
      `new Promise((resolve) => {
        const audio = document.getElementById("startup-audio");
        if (!audio) {
          resolve({ played: false, reason: "audio file missing" });
          return;
        }

        let settled = false;
        const finish = (result) => {
          if (settled) return;
          settled = true;
          window.clearTimeout(timer);
          resolve(result);
        };

        const timer = window.setTimeout(() => finish({ played: false, reason: "audio timeout" }), ${timeoutMs});
        audio.volume = 1;
        audio.currentTime = 0;
        audio.addEventListener("ended", () => finish({ played: true, reason: "ended" }), { once: true });
        audio.addEventListener("error", () => finish({ played: false, reason: "audio error" }), { once: true });

        audio.play().then(() => {
          if (audio.ended) finish({ played: true, reason: "ended" });
        }).catch(() => {
          const message = document.querySelector("p");
          if (message) message.textContent = "CLICK ONCE TO PLAY STARTUP AUDIO";
          window.addEventListener("pointerdown", () => {
            audio.play().catch(() => finish({ played: false, reason: "audio blocked" }));
          }, { once: true });
        });
      })`,
      true,
    );
  } catch (error) {
    return { played: false, reason: error.message };
  }
}

module.exports = { createSplashWindow, waitForStartupAudio };
