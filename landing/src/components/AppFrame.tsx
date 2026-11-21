"use client";

import React, { ReactNode } from "react";
import { motion } from "framer-motion";
import ThemeToggle from "./ThemeToggle";

interface AppFrameProps {
  children: ReactNode;
  activeView: string;
}

export default function AppFrame({ children, activeView }: AppFrameProps) {
  return (
    <motion.div
      initial={{ scale: 0.94, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ duration: 0.8, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
      className="glass active-pulse"
      style={{
        width: "100%",
        height: "100%",
        borderRadius: "16px",
        overflow: "hidden",
        display: "flex",
        flexDirection: "column",
        boxShadow: "var(--color-frame-shadow)",
        zIndex: 10,
        position: "relative",
      }}
    >
      {/* OS Window Header Chrome */}
      <div
        style={{
          height: "44px",
          borderBottom: "1px solid var(--color-border)",
          background: "var(--color-frame-header)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0 18px",
          position: "relative",
          zIndex: 11,
          transition: "background 0.3s ease, border-color 0.3s ease",
        }}
      >
        {/* Linux GNOME / macOS style circles */}
        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          <div style={{ width: "11px", height: "11px", borderRadius: "50%", background: "var(--color-accent-red)", opacity: 0.85 }} />
          <div style={{ width: "11px", height: "11px", borderRadius: "50%", background: "#fbbf24", opacity: 0.85 }} />
          <div style={{ width: "11px", height: "11px", borderRadius: "50%", background: "var(--color-accent-green)", opacity: 0.85 }} />
        </div>

        {/* Title status - centered */}
        <div
          style={{
            position: "absolute",
            left: "50%",
            transform: "translateX(-50%)",
            fontSize: "11px",
            fontWeight: 500,
            color: "var(--color-text-secondary)",
            letterSpacing: "0.05em",
            textTransform: "uppercase",
            fontFamily: "var(--font-jetbrains-mono), monospace",
            display: "flex",
            alignItems: "center",
            gap: "8px",
            pointerEvents: "none",
          }}
        >
          <img
            src="/trackora_logo.png"
            alt="Trackora"
            style={{
              width: "12px",
              height: "12px",
              objectFit: "contain",
              flexShrink: 0,
            }}
          />
          <span style={{ fontWeight: 800 }}>TRACKORA</span>
          <span style={{ color: "var(--color-text-muted)" }}>•</span>
          <span style={{ color: "var(--color-accent-blue)" }}>{activeView}</span>
        </div>

        {/* Right side window controls: Theme Toggle */}
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <ThemeToggle size="sm" />
        </div>
      </div>

      {/* Main workspace splits */}
      <div
        style={{
          flex: 1,
          display: "flex",
          overflow: "hidden",
          position: "relative",
        }}
      >
        {children}
      </div>
    </motion.div>
  );
}
