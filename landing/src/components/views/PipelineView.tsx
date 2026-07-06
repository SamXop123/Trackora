"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { Network, ArrowRight, Layers, Cpu, Server, Database, AppWindow } from "lucide-react";

interface PipelineViewProps {
  onComplete: () => void;
}

const LAYERS = [
  {
    id: "wayland",
    name: "The Window",
    desc: "Every app you open, tab you switch, or document you read is a moment of focused attention.",
    icon: Layers,
    color: "#9ca3af",
    benefit: "Whether you are writing, designing, coding, or playing music, every focus switch is captured cleanly so you don't have to keep track of it manually.",
    technical: "Standard user processes are isolated from Mutter's display compositor. A sandboxed process cannot see other focused application classes.",
  },
  {
    id: "extension",
    name: "The Observer",
    desc: "A secure system observer tracks focus changes in real-time without compromising display security.",
    icon: Cpu,
    color: "#3b82f6",
    benefit: "Operates directly at the system-compositor level. This means it queries metadata securely without letting other apps spy on your screen.",
    technical: "Uses global.display.get_focus_window() to extract focused wm_class and window title properties every 3 seconds.",
  },
  {
    id: "json",
    name: "The Courier",
    desc: "Focus updates are sent atomically to a local storage container without locking your system files.",
    icon: Server,
    color: "#10b981",
    benefit: "Uses safe, non-contending file updates so that there are no delays or file locking issues, keeping background resources near zero.",
    technical: "Uses GLib atomic write flags (REPLACE_DESTINATION) to update current_window.json, bypassing read-lock contention.",
  },
  {
    id: "daemon",
    name: "The Engine",
    desc: "A background companion groups session durations, filters out short distractions, and respects idle time when you walk away.",
    icon: Cpu,
    color: "#f97316",
    benefit: "Runs quietly as a system user service. It detects when you walk away for a coffee and stops the timer, ensuring your analytics are completely accurate.",
    technical: "Runs as a systemd user service. Evaluates session time, filters out noise under 10 seconds, and tracks single-instance locks.",
  },
  {
    id: "sqlite",
    name: "The Vault",
    desc: "Your history is saved locally in an offline file database on your own machine. No accounts, no cloud, no leaks.",
    icon: Database,
    color: "#a855f7",
    benefit: "Your database is a simple file on your hard drive. You can copy it, delete it, or inspect it. No data ever leaves your computer.",
    technical: "Applies idx_app_sessions_single_open indices. Closed rows hold duration; startup checks close stale open records.",
  },
  {
    id: "gui",
    name: "The Interface",
    desc: "An elegant desktop dashboard organizes your raw session metrics into visual habit trends on demand.",
    icon: AppWindow,
    color: "#3b82f6",
    benefit: "A premium desktop view built with dark, HSL color tokens and custom micro-animations that refresh dynamically to help you understand your day.",
    technical: "MainWindow drives QStackedWidget pages. QTimer triggers refresh increments while paintEvents animate HSL themes.",
  },
];

export default function PipelineView({ onComplete }: PipelineViewProps) {
  const [activeLayer, setActiveLayer] = useState(1); // default to observer layer
  const [showTech, setShowTech] = useState(false);

  const currentLayer = LAYERS[activeLayer];
  const LayerIcon = currentLayer.icon;

  return (
    <div
      style={{
        flex: 1,
        height: "100%",
        display: "flex",
        padding: "40px",
        gap: "40px",
        alignItems: "center",
        justifyContent: "space-between",
        background: "rgba(10, 15, 24, 0.4)",
        overflow: "hidden",
      }}
    >
      {/* Left panel: Detailed Technical Specs */}
      <div
        style={{
          width: "48%",
          display: "flex",
          flexDirection: "column",
          gap: "20px",
          textAlign: "left",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <Network size={16} style={{ color: "var(--color-accent-blue)" }} />
          <span style={{ fontSize: "11px", fontWeight: 800, letterSpacing: "0.1em", color: "var(--color-text-secondary)" }}>
            INSIDE TRACKORA
          </span>
        </div>

        <div>
          <span style={{ fontSize: "10px", fontFamily: "var(--font-jetbrains-mono), monospace", color: "var(--color-text-muted)" }}>
            LAYER SPECIFICATION
          </span>
          <h2
            style={{
              fontSize: "28px",
              fontWeight: 800,
              color: "var(--color-text-primary)",
              marginTop: "4px",
              display: "flex",
              alignItems: "center",
              gap: "10px",
            }}
          >
            <LayerIcon size={24} style={{ color: currentLayer.color }} />
            <span>{currentLayer.name}</span>
          </h2>
        </div>

        <p style={{ fontSize: "13px", color: "var(--color-text-secondary)", lineHeight: "1.6" }}>
          {currentLayer.desc}
        </p>

        {/* Technical / Benefit notes callout */}
        <div
          className="glass"
          style={{
            padding: "16px",
            borderRadius: "10px",
            background: "rgba(255, 255, 255, 0.01)",
            borderLeft: `3px solid ${currentLayer.color}`,
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
            <span style={{ fontSize: "9px", fontFamily: "var(--font-jetbrains-mono), monospace", color: "var(--color-text-muted)", fontWeight: 700, letterSpacing: "0.06em" }}>
              {showTech ? "COMPILED TECHNICAL DETAILS" : "USER BENEFIT SUMMARY"}
            </span>
            <button
              onClick={() => setShowTech(!showTech)}
              style={{
                background: "transparent",
                border: "none",
                color: "var(--color-accent-blue)",
                fontSize: "9px",
                fontWeight: 700,
                cursor: "pointer",
                outline: "none",
                fontFamily: "var(--font-jetbrains-mono), monospace",
              }}
            >
              {showTech ? "SHOW BENEFIT" : "FOR DEVELOPERS"}
            </button>
          </div>
          <div style={{ fontSize: "11px", color: "var(--color-text-primary)", fontFamily: "var(--font-jetbrains-mono), monospace", lineHeight: "1.5" }}>
            {showTech ? currentLayer.technical : currentLayer.benefit}
          </div>
        </div>

        <div>
          <button
            onClick={onComplete}
            style={{
              background: "rgba(255, 255, 255, 0.03)",
              border: "1px solid var(--color-border)",
              color: "#ffffff",
              padding: "10px 20px",
              borderRadius: "8px",
              cursor: "pointer",
              fontSize: "11px",
              fontWeight: 700,
              display: "flex",
              alignItems: "center",
              gap: "8px",
              outline: "none",
            }}
          >
            <span>YOUR PRIVACY</span>
            <ArrowRight size={12} style={{ color: "var(--color-accent-blue)" }} />
          </button>
        </div>
      </div>

      {/* Right panel: Isometric Stack Simulator */}
      <div
        style={{
          width: "48%",
          height: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          position: "relative",
        }}
      >
        {/* Isometric projection wrapper */}
        <div
          style={{
            transform: "rotateX(60deg) rotateZ(-30deg)",
            transformStyle: "preserve-3d",
            display: "flex",
            flexDirection: "column",
            gap: "20px",
            position: "relative",
          }}
        >
          {LAYERS.map((layer, idx) => {
            const isActive = idx === activeLayer;
            const Icon = layer.icon;

            return (
              <motion.div
                key={layer.id}
                onClick={() => setActiveLayer(idx)}
                animate={{
                  translateZ: isActive ? 30 : 0,
                  boxShadow: isActive 
                    ? `0 10px 30px rgba(59, 130, 246, 0.25), 0 0 0 1px ${layer.color}`
                    : "0 5px 15px rgba(0, 0, 0, 0.2)",
                  backgroundColor: isActive ? "rgba(18, 24, 38, 0.85)" : "rgba(10, 15, 24, 0.6)",
                  borderColor: isActive ? layer.color : "var(--color-border)",
                }}
                transition={{ duration: 0.3 }}
                style={{
                  width: "220px",
                  height: "44px",
                  borderRadius: "8px",
                  border: "1px solid",
                  display: "flex",
                  alignItems: "center",
                  padding: "0 16px",
                  gap: "12px",
                  cursor: "pointer",
                  position: "relative",
                  transformStyle: "preserve-3d",
                }}
              >
                {/* Layer icon */}
                <Icon size={16} style={{ color: isActive ? layer.color : "var(--color-text-secondary)" }} />
                
                {/* Layer name */}
                <span
                  style={{
                    fontSize: "11px",
                    fontWeight: isActive ? 700 : 500,
                    color: isActive ? "var(--color-text-primary)" : "var(--color-text-secondary)",
                    fontFamily: "var(--font-jetbrains-mono), monospace",
                  }}
                >
                  {layer.name}
                </span>

                {/* Simulated vertical connection line */}
                {idx < LAYERS.length - 1 && (
                  <div
                    style={{
                      position: "absolute",
                      bottom: "-20px",
                      left: "30px",
                      width: "1px",
                      height: "20px",
                      borderLeft: "1px dashed var(--color-border)",
                      pointerEvents: "none",
                    }}
                  />
                )}

                {/* Animated data packet traveling down active layer */}
                {isActive && (
                  <motion.div
                    initial={{ top: "-10px", opacity: 0 }}
                    animate={{ top: "44px", opacity: [0, 1, 1, 0] }}
                    transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
                    style={{
                      position: "absolute",
                      left: "30px",
                      width: "3px",
                      height: "10px",
                      borderRadius: "1.5px",
                      background: layer.color,
                      boxShadow: `0 0 8px ${layer.color}`,
                      zIndex: 10,
                    }}
                  />
                )}
              </motion.div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
