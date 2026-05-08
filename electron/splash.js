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
  const startupWav = path.join(resourceRoot, "assets", "sounds", "startup.wav");
  const startupMp3 = path.join(resourceRoot, "assets", "sounds", "startup.mp3");
  const logoPng = path.join(resourceRoot, "assets", "logo.png");
  const startupSound = fs.existsSync(startupWav) ? startupWav : fs.existsSync(startupMp3) ? startupMp3 : "";
  const soundSrc = startupSound ? pathToFileURL(startupSound).toString() : "";
  const logoSrc = fs.existsSync(logoPng)
    ? `data:image/png;base64,${fs.readFileSync(logoPng).toString("base64")}`
    : "";

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
        background:
          radial-gradient(circle at 50% 0%, rgba(0,229,255,.13), transparent 34%),
          radial-gradient(circle at 80% 20%, rgba(99,102,241,.13), transparent 30%),
          #070B14;
        color: #E6EDF3;
        font-family: Inter, "Segoe UI", Arial, sans-serif;
        opacity: 1;
        transition: opacity 520ms ease, transform 520ms ease, filter 520ms ease;
      }
      body.fade-out {
        opacity: 0;
        transform: scale(.985);
        filter: blur(8px);
      }
      body::before {
        content: "";
        position: fixed;
        inset: 0;
        opacity: .045;
        background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 240 240' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.8' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='240' height='240' filter='url(%23n)' opacity='.55'/%3E%3C/svg%3E");
      }
      .shell {
        position: relative;
        display: grid;
        place-items: center;
        width: 100vw;
        height: 100vh;
        border: 1px solid rgba(255,255,255,.06);
      }
      .content {
        width: 420px;
        text-align: center;
        animation: scene .7s ease-out both;
      }
      .logo {
        position: relative;
        display: grid;
        place-items: center;
        width: 92px;
        height: 92px;
        margin: 0 auto;
        border: 1px solid rgba(255,255,255,.08);
        border-radius: 28px;
        background: rgba(15,23,42,.72);
        box-shadow: 0 24px 80px rgba(0,0,0,.35), 0 0 54px rgba(0,229,255,.12);
        animation: logoIn .8s .25s ease-out both, pulse 3.2s 1.2s ease-in-out infinite;
        overflow: hidden;
      }
      .logo img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        display: block;
      }
      h1 {
        margin: 26px 0 0;
        font-size: 30px;
        font-weight: 650;
        letter-spacing: -.04em;
        animation: fadeUp .65s .65s ease-out both;
      }
      .subtitle {
        margin: 8px 0 0;
        color: #94A3B8;
        font-size: 15px;
        animation: fadeUp .65s .8s ease-out both;
      }
      .status {
        margin-top: 28px;
        color: #94A3B8;
        font-size: 13px;
        animation: fadeUp .65s 1s ease-out both;
      }
      .loader {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 5px;
        height: 36px;
        margin: 16px auto 0;
        animation: fadeUp .65s 1.1s ease-out both;
      }
      .loader span {
        width: 4px;
        height: 10px;
        border-radius: 999px;
        background: #00E5FF;
        opacity: .3;
        animation: wave 1s ease-in-out infinite;
      }
      .loader span:nth-child(2) { animation-delay: .08s; }
      .loader span:nth-child(3) { animation-delay: .16s; }
      .loader span:nth-child(4) { animation-delay: .24s; }
      .loader span:nth-child(5) { animation-delay: .32s; }
      .items {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 8px;
        margin-top: 34px;
        animation: fadeUp .65s 1.35s ease-out both;
      }
      .item {
        border: 1px solid rgba(255,255,255,.06);
        border-radius: 16px;
        background: rgba(255,255,255,.035);
        padding: 11px 8px;
        color: #94A3B8;
        font-size: 12px;
      }
      .dot {
        display: block;
        width: 6px;
        height: 6px;
        margin: 0 auto 7px;
        border-radius: 50%;
        background: #00E5FF;
        box-shadow: 0 0 18px rgba(0,229,255,.35);
      }
      @keyframes scene {
        from { opacity: 0; transform: scale(.985); }
        to { opacity: 1; transform: scale(1); }
      }
      @keyframes logoIn {
        from { opacity: 0; transform: translateY(8px) scale(.95); }
        to { opacity: 1; transform: translateY(0) scale(1); }
      }
      @keyframes fadeUp {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
      }
      @keyframes pulse {
        0%, 100% { box-shadow: 0 24px 80px rgba(0,0,0,.35), 0 0 44px rgba(0,229,255,.1); }
        50% { box-shadow: 0 24px 80px rgba(0,0,0,.35), 0 0 68px rgba(0,229,255,.18); }
      }
      @keyframes wave {
        0%, 100% { height: 9px; opacity: .35; }
        50% { height: 24px; opacity: .95; }
      }
    </style>
  </head>
  <body>
    <div class="shell">
      <div class="content">
        <div class="logo">${logoSrc ? `<img src="${logoSrc}" alt="JX Jarvis logo" />` : "JX"}</div>
        <h1>JX Jarvis</h1>
        <p class="subtitle">Personal AI Workspace</p>
        <p class="status">Initializing systems...</p>
        <div class="loader" aria-hidden="true">
          <span></span><span></span><span></span><span></span><span></span>
        </div>
        <div class="items">
          <div class="item"><span class="dot"></span>Secure</div>
          <div class="item"><span class="dot"></span>Voice Engine</div>
          <div class="item"><span class="dot"></span>Memory</div>
          <div class="item"><span class="dot"></span>Workspace</div>
        </div>
      </div>
    </div>
    ${
      soundSrc
        ? `<audio id="startup-audio" src="${soundSrc}" autoplay preload="auto"></audio>
    <script>
      const audio = document.getElementById("startup-audio");
      window.__startupAudioStarted = false;
      window.__startupAudioPlaying = false;
      window.__startupAudioFailed = false;
      window.__startupAudioSettled = false;
      window.__startupAudioPromise = null;

      window.startStartupAudioOnce = function startStartupAudioOnce() {
        if (!audio) return Promise.resolve({ played: false, reason: "audio missing" });
        if (window.__startupAudioPromise) return window.__startupAudioPromise;

        audio.volume = 0.72;
        audio.preload = "auto";

        window.__startupAudioPromise = new Promise((resolve) => {
          const finish = (result) => {
            if (window.__startupAudioSettled) return;
            window.__startupAudioSettled = true;
            resolve(result);
          };

          audio.addEventListener("playing", () => {
            window.__startupAudioPlaying = true;
          });
          audio.addEventListener("error", () => {
            window.__startupAudioFailed = true;
          });
          audio.addEventListener("ended", () => finish({ played: true, reason: "ended" }), { once: true });

          const play = () => {
            if (window.__startupAudioStarted || window.__startupAudioSettled) return;
            window.__startupAudioStarted = true;
            audio.currentTime = 0;
            audio.play().catch(() => {
              window.__startupAudioStarted = false;
              window.setTimeout(play, 450);
              window.setTimeout(play, 1400);
            });
          };

          play();
        });
        return window.__startupAudioPromise;
      };

      window.startStartupAudioOnce();
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
  const preferredIcon = path.join(resourceRoot, "assets", "jx-jarvis.ico");
  const fallbackIcon = path.join(resourceRoot, "assets", "icon.ico");
  const icon = fs.existsSync(preferredIcon) ? preferredIcon : fallbackIcon;
  const splash = new BrowserWindow({
    width: 620,
    height: 460,
    frame: false,
    transparent: false,
    resizable: false,
    show: false,
    backgroundColor: "#070B14",
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

async function waitForStartupAudio(splash, timeoutMs = 9000) {
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
          window.setTimeout(() => resolve({ played: false, reason: "audio file missing" }), ${timeoutMs});
          return;
        }

        let waitSettled = false;
        const finish = (result) => {
          if (waitSettled) return;
          waitSettled = true;
          window.clearTimeout(timer);
          resolve(result);
        };

        const timer = window.setTimeout(() => {
          const playbackStarted = window.__startupAudioPlaying || (!audio.paused && audio.currentTime > 0);
          if (!playbackStarted || window.__startupAudioFailed) {
            finish({ played: false, reason: "audio timeout" });
          }
        }, ${timeoutMs});
        if (audio.ended || window.__startupAudioSettled) {
          finish({ played: true, reason: "ended" });
          return;
        }

        if (typeof window.startStartupAudioOnce === "function") {
          window.startStartupAudioOnce().then(finish).catch(() => {});
        } else {
          audio.volume = .72;
          audio.addEventListener("ended", () => finish({ played: true, reason: "ended" }), { once: true });
          audio.play().catch(() => {});
        }
      })`,
      true,
    );
  } catch (error) {
    return { played: false, reason: error.message };
  }
}

async function fadeOutSplash(splash, durationMs = 560) {
  if (!splash || splash.isDestroyed()) return;

  try {
    await splash.webContents.executeJavaScript(
      `new Promise((resolve) => {
        document.body.classList.add("fade-out");
        window.setTimeout(resolve, ${durationMs});
      })`,
      true,
    );
  } catch {
    await new Promise((resolve) => setTimeout(resolve, durationMs));
  }
}

module.exports = { createSplashWindow, waitForStartupAudio, fadeOutSplash };
