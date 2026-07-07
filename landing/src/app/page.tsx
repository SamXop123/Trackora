"use client";

import React, { useState, useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import Starfield from "../components/Starfield";
import AppFrame from "../components/AppFrame";
import Sidebar from "../components/Sidebar";
import CommandPalette from "../components/CommandPalette";

// Views
import IntroView from "../components/views/IntroView";
import ReplayView from "../components/views/ReplayView";
import DashboardView from "../components/views/DashboardView";
import PipelineView from "../components/views/PipelineView";
import PrivacyView from "../components/views/PrivacyView";
import DownloadView from "../components/views/DownloadView";

const VIEW_ORDER = ["intro", "replay", "dashboard", "pipeline", "privacy", "download"];

export default function Home() {
  const [activeView, setActiveView] = useState("intro");
  const [warpActive, setWarpActive] = useState(false);
  const [lastScrollTime, setLastScrollTime] = useState(0);

  // Scroll-linking navigation
  useEffect(() => {
    const handleWheel = (e: WheelEvent) => {
      if (e.ctrlKey) return; // Ignore browser zoom scroll wheel gestures
      const now = Date.now();
      if (now - lastScrollTime < 1000) return; // Debounce scroll transitions

      const currentIndex = VIEW_ORDER.indexOf(activeView);
      if (e.deltaY > 30) {
        // Scroll down -> next scene
        if (currentIndex < VIEW_ORDER.length - 1) {
          setActiveView(VIEW_ORDER[currentIndex + 1]);
          setLastScrollTime(now);
        }
      } else if (e.deltaY < -30) {
        // Scroll up -> previous scene
        if (currentIndex > 0) {
          setActiveView(VIEW_ORDER[currentIndex - 1]);
          setLastScrollTime(now);
        }
      }
    };

    window.addEventListener("wheel", handleWheel);
    return () => window.removeEventListener("wheel", handleWheel);
  }, [activeView, lastScrollTime]);

  const handleNavigate = (view: string) => {
    if (VIEW_ORDER.includes(view)) {
      setActiveView(view);
    }
  };

  const handleToggleWarp = () => {
    setWarpActive((prev) => !prev);
  };

  return (
    <main
      style={{
        width: "100vw",
        height: "100vh",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        overflow: "hidden",
        position: "relative",
        background: "#05070a",
        padding: "40px",
      }}
    >
      {/* Background Starfield with warp speed Easter Egg */}
      <Starfield warpActive={warpActive} />

      {/* Keyboard Command palette */}
      <CommandPalette onNavigate={handleNavigate} onToggleWarp={handleToggleWarp} />

      {/* Primary Desktop Frame */}
      <AppFrame activeView={activeView.toUpperCase()}>
        {/* Sidebar */}
        <Sidebar activeView={activeView} onNavigate={handleNavigate} />

        {/* Viewport page stack */}
        <div
          style={{
            flex: 1,
            height: "100%",
            overflow: "hidden",
            position: "relative",
          }}
        >
          <AnimatePresence mode="wait">
            {activeView === "intro" && (
              <motion.div
                key="intro"
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.98 }}
                transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
                style={{ width: "100%", height: "100%" }}
              >
                <IntroView onStartReplay={() => setActiveView("replay")} onNavigateDownload={() => setActiveView("download")} />
              </motion.div>
            )}

            {activeView === "replay" && (
              <motion.div
                key="replay"
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.98 }}
                transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
                style={{ width: "100%", height: "100%" }}
              >
                <ReplayView onComplete={() => setActiveView("dashboard")} />
              </motion.div>
            )}

            {activeView === "dashboard" && (
              <motion.div
                key="dashboard"
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.98 }}
                transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
                style={{ width: "100%", height: "100%" }}
              >
                <DashboardView onComplete={() => setActiveView("pipeline")} />
              </motion.div>
            )}

            {activeView === "pipeline" && (
              <motion.div
                key="pipeline"
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.98 }}
                transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
                style={{ width: "100%", height: "100%" }}
              >
                <PipelineView onComplete={() => setActiveView("privacy")} />
              </motion.div>
            )}

            {activeView === "privacy" && (
              <motion.div
                key="privacy"
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.98 }}
                transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
                style={{ width: "100%", height: "100%" }}
              >
                <PrivacyView onComplete={() => setActiveView("download")} />
              </motion.div>
            )}

            {activeView === "download" && (
              <motion.div
                key="download"
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.98 }}
                transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
                style={{ width: "100%", height: "100%" }}
              >
                <DownloadView />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </AppFrame>
    </main>
  );
}
