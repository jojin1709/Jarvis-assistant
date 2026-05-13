export function accessibilityState() {
  return {
    reducedMotion: window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches || false,
    highContrast: window.matchMedia?.("(prefers-contrast: more)")?.matches || false,
  };
}
