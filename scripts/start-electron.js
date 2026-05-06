const path = require("node:path");
const { spawn } = require("node:child_process");
const electronPath = require("electron");

const projectRoot = path.join(__dirname, "..");
const env = {
  ...process.env,
  VITE_DEV_SERVER_URL: process.env.VITE_DEV_SERVER_URL || "http://127.0.0.1:5173",
};

delete env.ELECTRON_RUN_AS_NODE;

const child = spawn(electronPath, [projectRoot], {
  cwd: projectRoot,
  env,
  stdio: "inherit",
  windowsHide: false,
});

child.on("exit", (code) => process.exit(code ?? 0));
