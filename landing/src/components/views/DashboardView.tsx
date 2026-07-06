"use client";

import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sliders, Clock, BarChart3, AppWindow, ArrowRight } from "lucide-react";

interface DashboardViewProps {
  onComplete: () => void;
}

const APPS_METRICS = [
  { name: "Brave Browser", duration: "2h 18m", pct: 40, color: "#f97316", detail: "Researching reference APIs and design assets." },
  { name: "Minecraft", duration: "1h 30m", pct: 26, color: "#10b981", detail: "Playing Minecraft. Creative sandbox session." },
  { name: "VS Code", duration: "56m", pct: 16, color: "#3b82f6", detail: "Writing code. Refining database sync logic." },
  { name: "YouTube", duration: "46m", pct: 13, color: "#ff0000", detail: "Watching design showcases and keynotes in browser." },
  { name: "Spotify", duration: "15m", pct: 5, color: "#1db954", detail: "Listening to focus beats and ambient audio." },
];

export default function DashboardView({ onComplete }: DashboardViewProps) {
  const [seconds, setSeconds] = useState(0);
  const [minutes, setMinutes] = useState(45);
  const [hours, setHours] = useState(5);
  const [activeHoverApp, setActiveHoverApp] = useState<number | null>(null);

  useEffect(() => {
    const timer = setInterval(() => {
      setSeconds((s) => {
        if (s >= 59) {
          setMinutes((m) => {
            if (m >= 59) {
              setHours((h) => h + 1);
              return 0;
            }
            return m + 1;
          });
          return 0;
        }
        return s + 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  return (
    <div
      style={{
        flex: 1,
        height: "100%",
        display: "flex",
        flexDirection: "column",
        padding: "30px",
        gap: "24px",
        background: "rgba(10, 15, 24, 0.2)",
        overflow: "hidden",
        position: "relative",
      }}
    >
      {/* Page Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <Clock size={16} style={{ color: "var(--color-accent-blue)" }} />
          <span style={{ fontSize: "11px", fontWeight: 800, letterSpacing: "0.1em", color: "var(--color-text-secondary)" }}>
            WHAT PATTERNS ARE YOU MISSING?
          </span>
        </div>

        <button
          onClick={onComplete}
          style={{
            background: "transparent",
            border: "none",
            color: "var(--color-accent-blue)",
            fontSize: "10px",
            fontWeight: 700,
            display: "flex",
            alignItems: "center",
            gap: "6px",
            cursor: "pointer",
            outline: "none",
          }}
        >
          <span>INSIDE TRACKORA</span>
          <ArrowRight size={12} />
        </button>
      </div>

      {/* Grid splits */}
      <div style={{ display: "flex", gap: "20px", flex: 1, overflow: "hidden" }}>
        {/* Left Column: Big Screen Time Hero */}
        <div
          style={{
            width: "45%",
            display: "flex",
            flexDirection: "column",
            gap: "20px",
          }}
        >
          {/* Hero Card */}
          <div
            className="glass"
            style={{
              flex: 1,
              borderRadius: "14px",
              padding: "24px",
              display: "flex",
              flexDirection: "column",
              justifyContent: "space-between",
              position: "relative",
              overflow: "hidden",
            }}
          >
            {/* Ambient inner radial glow */}
            <div
              style={{
                position: "absolute",
                top: "-40px",
                right: "-40px",
                width: "160px",
                height: "160px",
                borderRadius: "50%",
                background: "radial-gradient(circle, rgba(59, 130, 246, 0.12) 0%, rgba(59, 130, 246, 0) 70%)",
                pointerEvents: "none",
              }}
            />

            <div>
              <div style={{ fontSize: "10px", fontWeight: 700, color: "var(--color-accent-blue)", letterSpacing: "0.08em" }}>
                TODAY
              </div>
              <div
                style={{
                  fontSize: "44px",
                  fontWeight: 800,
                  letterSpacing: "-0.04em",
                  color: "var(--color-text-primary)",
                  marginTop: "8px",
                  fontFamily: "var(--font-jetbrains-mono), monospace",
                }}
              >
                {hours}h {minutes}m <span style={{ color: "var(--color-accent-blue)" }}>{seconds.toString().padStart(2, "0")}s</span>
              </div>
              <div style={{ fontSize: "11px", color: "var(--color-text-secondary)", marginTop: "4px" }}>
                Total Screen Time Today
              </div>
            </div>

            {/* Micro stats indicators */}
            <div style={{ display: "flex", gap: "20px", borderTop: "1px solid var(--color-border)", paddingTop: "16px" }}>
              <div>
                <div style={{ fontSize: "10px", color: "var(--color-text-muted)" }}>YESTERDAY</div>
                <div style={{ fontSize: "14px", fontWeight: 700, color: "var(--color-text-secondary)", marginTop: "2px" }}>
                  4h 12m
                </div>
              </div>
              <div style={{ borderLeft: "1px solid var(--color-border)", paddingLeft: "20px" }}>
                <div style={{ fontSize: "10px", color: "var(--color-text-muted)" }}>FOCUS SCORE</div>
                <div style={{ fontSize: "14px", fontWeight: 700, color: "var(--color-accent-green)", marginTop: "2px" }}>
                  87%
                </div>
              </div>
            </div>
          </div>

          {/* Micro Mini-Chart */}
          <div
            className="glass"
            style={{
              height: "130px",
              borderRadius: "14px",
              padding: "16px 20px",
              display: "flex",
              flexDirection: "column",
              gap: "12px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "10px", fontWeight: 700, color: "var(--color-text-secondary)" }}>
              <BarChart3 size={12} />
              <span>HOURLY DISTRIBUTION</span>
            </div>
            
            {/* Mini bars */}
            <div style={{ display: "flex", alignItems: "flex-end", justifySelf: "flex-end", flex: 1, gap: "8px" }}>
              {[15, 30, 10, 45, 80, 60, 25, 90, 40, 15].map((val, idx) => (
                <div key={idx} style={{ flex: 1, display: "flex", flexDirection: "column", gap: "4px", alignItems: "center" }}>
                  <motion.div
                    initial={{ height: 0 }}
                    animate={{ height: `${val * 0.6}px` }}
                    transition={{ duration: 1, delay: idx * 0.05, ease: "easeOut" }}
                    style={{
                      width: "100%",
                      borderRadius: "2px",
                      background: idx === 7 ? "var(--color-accent-blue)" : "rgba(255, 255, 255, 0.06)",
                      boxShadow: idx === 7 ? "0 0 10px rgba(59, 130, 246, 0.4)" : "none",
                    }}
                  />
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Applications Breakdown */}
        <div
          className="glass"
          style={{
            width: "55%",
            borderRadius: "14px",
            padding: "24px",
            display: "flex",
            flexDirection: "column",
            gap: "20px",
            overflowY: "auto",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "11px", fontWeight: 700, color: "var(--color-text-secondary)" }}>
            <AppWindow size={13} />
            <span>TOP APPLICATIONS</span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            {APPS_METRICS.map((app, idx) => {
              const isHovered = activeHoverApp === idx;
              return (
                <div
                  key={app.name}
                  onMouseEnter={() => setActiveHoverApp(idx)}
                  onMouseLeave={() => setActiveHoverApp(null)}
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "6px",
                    cursor: "pointer",
                    padding: "6px",
                    borderRadius: "8px",
                    background: isHovered ? "rgba(255, 255, 255, 0.02)" : "transparent",
                    transition: "background 0.2s ease",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <div
                        style={{
                          width: "8px",
                          height: "8px",
                          borderRadius: "50%",
                          background: app.color,
                        }}
                      />
                      <span style={{ fontSize: "12px", fontWeight: 700, color: "var(--color-text-primary)" }}>
                        {app.name}
                      </span>
                    </div>
                    <span style={{ fontSize: "11px", fontWeight: 600, color: "var(--color-text-secondary)", fontFamily: "var(--font-jetbrains-mono), monospace" }}>
                      {app.duration}
                    </span>
                  </div>

                  {/* Progress Bar Container */}
                  <div style={{ width: "100%", height: "4px", background: "rgba(255, 255, 255, 0.04)", borderRadius: "2px", overflow: "hidden" }}>
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${app.pct}%` }}
                      transition={{ duration: 1.2, delay: 0.1 }}
                      style={{
                        height: "100%",
                        background: app.color,
                      }}
                    />
                  </div>

                  {/* Expand window title on hover */}
                  <div style={{ height: "14px", overflow: "hidden" }}>
                    <AnimatePresence>
                      {isHovered && (
                        <motion.div
                          initial={{ opacity: 0, y: -4 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0, y: -4 }}
                          transition={{ duration: 0.15 }}
                          style={{
                            fontSize: "9px",
                            fontFamily: "var(--font-jetbrains-mono), monospace",
                            color: "var(--color-text-muted)",
                            textAlign: "left",
                            paddingLeft: "16px",
                          }}
                        >
                          {app.detail}
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
