import React, { useEffect } from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import "./index.css";

import { cleanupExpiredConfirmations } from "./lib/localStorage";
import { applyTheme, getThemePreference } from "./lib/theme";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Runs from "./pages/Runs";
import RunDetails from "./pages/RunDetails";
import Portfolio from "./pages/Portfolio";
import Settings from "./pages/Settings";

const queryClient = new QueryClient();

function App() {
  useEffect(() => {
    // Cleanup expired localStorage entries on mount
    cleanupExpiredConfirmations();

    const applyCurrentTheme = () => applyTheme(getThemePreference());
    applyCurrentTheme();

    const onThemeChange = () => applyCurrentTheme();
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const onMediaChange = () => {
      if (getThemePreference() === "system") {
        applyCurrentTheme();
      }
    };

    window.addEventListener("momentor-theme-change", onThemeChange);
    if (media.addEventListener) {
      media.addEventListener("change", onMediaChange);
    } else {
      media.addListener(onMediaChange);
    }

    return () => {
      window.removeEventListener("momentor-theme-change", onThemeChange);
      if (media.removeEventListener) {
        media.removeEventListener("change", onMediaChange);
      } else {
        media.removeListener(onMediaChange);
      }
    };
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="runs" element={<Runs />} />
            <Route path="runs/:runId" element={<RunDetails />} />
            <Route path="portfolio" element={<Portfolio />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
