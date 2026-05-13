export function subscribeToGlobalVoice(callback) {
  if (!window.jxJarvis?.onVoiceEvent) return () => {};
  return window.jxJarvis.onVoiceEvent(callback);
}

export function triggerGlobalPushToTalk() {
  if (!window.jxJarvis?.pushToTalk) return Promise.resolve(null);
  return window.jxJarvis.pushToTalk();
}

export function setElectronVoiceRuntime(patch) {
  if (!window.jxJarvis?.setVoiceRuntime) return Promise.resolve(null);
  return window.jxJarvis.setVoiceRuntime(patch);
}
