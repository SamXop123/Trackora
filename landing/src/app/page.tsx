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

      {/* Crawlable Semantic SEO & GEO Structured Content Layer for Search Engines and AI Indexers */}
      <section className="sr-only" aria-label="About Trackora Screen Time and Productivity Tracker">
        <header>
          <h1>Trackora — Free & Local-First Screen Time Tracker for Windows and Linux</h1>
          <p>
            Trackora is a privacy-first, open-source desktop screen time and activity tracker built for Windows 10/11 and Linux (GNOME Wayland). It operates 100% offline with local SQLite storage, giving you automated time tracking, timeline replay, daily/weekly analytics charts, and zero telemetry.
          </p>
        </header>

        <article id="features">
          <h2>Key Features of Trackora Screen Time Tracker</h2>
          <ul>
            <li><strong>Automated Screen Time Tracking:</strong> Passively records active window focus with less than 0.1% CPU overhead.</li>
            <li><strong>100% Offline & Private:</strong> Zero telemetry, zero analytics tracking, and no cloud logins. All activity logs stay in your local SQLite database.</li>
            <li><strong>Daily & Weekly Analytics:</strong> Interactive bar charts, productivity ratios, session counts, and most-used application rankings.</li>
            <li><strong>Visual Activity Timeline:</strong> Replay and inspect exact application usage patterns throughout the day.</li>
            <li><strong>Intelligent Idle & AFK Detection:</strong> Automatically pauses tracking when you step away from keyboard and mouse, or when your system enters sleep or lock screen.</li>
            <li><strong>App Categorization:</strong> Automatically organizes usage across Browsers, Development, Communication, Music, Utilities, and System.</li>
            <li><strong>Productivity Goals:</strong> Define daily screen time limits or minimum productive focus targets.</li>
            <li><strong>System Tray Controls:</strong> Minimize to system tray and easily pause tracking for 15m, 30m, 1h, or custom durations.</li>
          </ul>
        </article>

        <article id="download">
          <h2>Download Trackora for Windows and Linux</h2>
          <p>Get started with Trackora today — completely free and open source.</p>
          <ul>
            <li><a href="/TrackoraSetup.exe" download>Download Trackora Installer for Windows (Windows 10 / Windows 11 64-bit)</a></li>
            <li><a href="/trackora-2.2.1.rpm" download>Download Trackora for Linux Fedora / RHEL (RPM Package)</a></li>
            <li><a href="https://github.com/SamXop123/Trackora">View Source Code on GitHub (MIT License)</a></li>
          </ul>
        </article>

        <article id="faq">
          <h2>Frequently Asked Questions (FAQ)</h2>
          <dl>
            <dt>What is Trackora?</dt>
            <dd>Trackora is a free, local-first screen time and activity tracker designed for desktop users on Windows and Linux who want deep productivity insights without compromising privacy.</dd>

            <dt>How is Trackora different from cloud-based time trackers?</dt>
            <dd>Unlike cloud trackers that send screenshots and keystrokes to third-party servers, Trackora keeps 100% of your data on your local device in an offline SQLite database. No account is required and no telemetry is transmitted.</dd>

            <dt>What platforms does Trackora support?</dt>
            <dd>Trackora supports Windows 10 and 11, as well as Linux distributions running GNOME Wayland (such as Fedora, Ubuntu, and Arch Linux).</dd>

            <dt>How does Trackora handle computer sleep and lock screen?</dt>
            <dd>Trackora monitors physical mouse and keyboard activity via native Win32/DBus hooks. When you lock your computer, close the lid, or step away for more than 5 minutes, tracking automatically halts to avoid logging false screen time.</dd>
          </dl>
        </article>

        <footer>
          <p>Trackora is created by the Trackora Open Source Team. Licensed under the MIT License.</p>
          <nav>
            <a href="https://github.com/SamXop123/Trackora">GitHub Repository</a> |{" "}
            <a href="/llms.txt">AI Documentation (llms.txt)</a> |{" "}
            <a href="/llms-full.txt">Full Technical Specs (llms-full.txt)</a>
          </nav>
        </footer>
      </section>
    </main>
  );
}
