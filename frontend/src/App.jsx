import { useEffect, useState } from "react";
import { HashRouter, Route, Routes } from "react-router-dom";

import AppShell from "./layouts/AppShell.jsx";
import AutomationPage from "./pages/AutomationPage.jsx";
import BrowserPage from "./pages/BrowserPage.jsx";
import ChatPage from "./pages/ChatPage.jsx";
import FilesPage from "./pages/FilesPage.jsx";
import HomePage from "./pages/HomePage.jsx";
import OnboardingPage from "./pages/OnboardingPage.jsx";
import SettingsPage from "./pages/SettingsPage.jsx";
import VoicePage from "./pages/VoicePage.jsx";
import { getProfile } from "./services/api.js";
import LogoMark from "./components/LogoMark.jsx";

export default function App() {
  const [profile, setProfile] = useState(null);
  const [checkingProfile, setCheckingProfile] = useState(true);
  const [backendUnavailable, setBackendUnavailable] = useState(false);

  useEffect(() => {
    let active = true;
    async function check() {
      try {
        const result = await getProfile();
        if (!active) return;
        setProfile(result.profile || null);
        setBackendUnavailable(false);
      } catch {
        if (!active) return;
        setBackendUnavailable(true);
      } finally {
        if (active) setCheckingProfile(false);
      }
    }
    check();
    return () => {
      active = false;
    };
  }, []);

  if (checkingProfile) {
    return <BootGate />;
  }

  if (!backendUnavailable && profile && !profile.onboarding_complete) {
    return (
      <OnboardingPage
        onComplete={(nextProfile, _permissions, setup) => {
          setProfile(nextProfile);
          window.localStorage.setItem("jx-jarvis-onboarding-theme", setup.theme.toLowerCase());
          if (setup.permissions.backgroundStartup && window.jxJarvis?.setOpenAtLogin) {
            window.jxJarvis.setOpenAtLogin(true);
          }
        }}
      />
    );
  }

  return (
    <HashRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<HomePage />} />
          <Route path="chat" element={<ChatPage />} />
          <Route path="voice" element={<VoicePage />} />
          <Route path="files" element={<FilesPage />} />
          <Route path="automation" element={<AutomationPage />} />
          <Route path="browser" element={<BrowserPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
      </Routes>
    </HashRouter>
  );
}

function BootGate() {
  return (
    <main className="grid min-h-screen place-items-center bg-void text-textPrimary">
      <div className="text-center">
        <LogoMark className="mx-auto h-14 w-14" rounded="rounded-2xl" />
        <p className="mt-4 text-sm text-textSecondary">Preparing your workspace...</p>
      </div>
    </main>
  );
}
