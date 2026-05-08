const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("jxJarvis", {
  platform: process.platform,
  minimize: () => ipcRenderer.send("window:minimize"),
  maximize: () => ipcRenderer.send("window:maximize"),
  close: () => ipcRenderer.send("window:close"),
  isMaximized: () => ipcRenderer.invoke("window:is-maximized"),
  getOpenAtLogin: () => ipcRenderer.invoke("system:get-open-at-login"),
  setOpenAtLogin: (enabled) => ipcRenderer.invoke("system:set-open-at-login", Boolean(enabled)),
  chooseFolder: () => ipcRenderer.invoke("system:choose-folder"),
  onGlobalCommand: (callback) => {
    const listener = (_event, command) => callback(command);
    ipcRenderer.on("global:command", listener);
    return () => ipcRenderer.removeListener("global:command", listener);
  },
  onWindowState: (callback) => {
    const listener = (_event, state) => callback(state);
    ipcRenderer.on("window:state", listener);
    return () => ipcRenderer.removeListener("window:state", listener);
  },
});
