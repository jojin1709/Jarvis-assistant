import { useEffect } from "react";

export function useKeyboardShortcuts({ onNewChat, onFocusChat, onToggleVoice }) {
  useEffect(() => {
    function handler(event) {
      const key = event.key.toLowerCase();
      if ((event.ctrlKey || event.metaKey) && key === "k") {
        event.preventDefault();
        onFocusChat?.();
      }
      if ((event.ctrlKey || event.metaKey) && event.shiftKey && key === "n") {
        event.preventDefault();
        onNewChat?.();
      }
      if ((event.ctrlKey || event.metaKey) && event.shiftKey && key === "v") {
        event.preventDefault();
        onToggleVoice?.();
      }
    }

    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onNewChat, onFocusChat, onToggleVoice]);
}
