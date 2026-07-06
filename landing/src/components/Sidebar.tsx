"use client";

import React from "react";
import { motion } from "framer-motion";
import { 
  Home, 
  History, 
  LayoutDashboard, 
  Network, 
  ShieldAlert, 
  Download, 
  Info,
  Sliders
} from "lucide-react";

interface SidebarProps {
  activeView: string;
  onNavigate: (view: string) => void;
}

const MENU_ITEMS = [
  { id: "intro", label: "Start", icon: Home },
  { id: "replay", label: "Your Day", icon: History },
  { id: "dashboard", label: "Your Habits", icon: LayoutDashboard },
  { id: "pipeline", label: "Inside Trackora", icon: Network },
  { id: "privacy", label: "Your Privacy", icon: ShieldAlert },
  { id: "download", label: "Get Started", icon: Download },
];

export default function Sidebar({ activeView, onNavigate }: SidebarProps) {
  return (
    <div
      style={{
        width: "210px",
        height: "100%",
        background: "rgba(10, 14, 22, 0.95)",
        borderRight: "1px solid var(--color-border)",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        padding: "20px 12px 14px 12px",
        flexShrink: 0,
        zIndex: 11,
      }}
    >
      {/* Branding and Nav Stack */}
      <div style={{ display: "flex", flexDirection: "column", gap: "28px" }}>
        {/* Brand header */}
        <div style={{ display: "flex", alignItems: "center", gap: "10px", paddingLeft: "8px" }}>
          <img
            src="/trackora_logo.png"
            alt="Trackora"
            style={{
              width: "20px",
              height: "20px",
              objectFit: "contain",
            }}
          />
          <span style={{ fontSize: "14px", fontWeight: 800, letterSpacing: "0.08em", color: "var(--color-text-primary)" }}>
            TRACKORA
          </span>
        </div>

        {/* Navigation list */}
        <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
          {MENU_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = activeView === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onNavigate(item.id)}
                style={{
                  width: "100%",
                  height: "38px",
                  background: "transparent",
                  border: "none",
                  borderRadius: "8px",
                  display: "flex",
                  alignItems: "center",
                  padding: "0 12px",
                  gap: "12px",
                  cursor: "pointer",
                  color: isActive ? "var(--color-text-primary)" : "var(--color-text-secondary)",
                  position: "relative",
                  textAlign: "left",
                  outline: "none",
                  transition: "color 0.2s ease",
                }}
              >
                {/* Active back glow */}
                {isActive && (
                  <motion.div
                    layoutId="active-nav-glow"
                    style={{
                      position: "absolute",
                      top: 0,
                      left: 0,
                      width: "100%",
                      height: "100%",
                      borderRadius: "8px",
                      background: "rgba(59, 130, 246, 0.08)",
                      border: "1px solid rgba(59, 130, 246, 0.15)",
                      zIndex: -1,
                    }}
                    transition={{ type: "spring", stiffness: 380, damping: 30 }}
                  />
                )}
                
                <Icon size={16} strokeWidth={isActive ? 2.5 : 2} style={{ color: isActive ? "var(--color-accent-blue)" : "inherit" }} />
                <span style={{ fontSize: "11px", fontWeight: isActive ? 700 : 500 }}>
                  {item.label}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Diagnostics / Tech stats widget */}
      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        {/* Download CTA Button */}
        <button
          onClick={() => onNavigate("download")}
          style={{
            width: "100%",
            background: "var(--color-accent-blue)",
            border: "1px solid rgba(59, 130, 246, 0.3)",
            color: "#ffffff",
            padding: "10px 12px",
            borderRadius: "8px",
            cursor: "pointer",
            fontSize: "11px",
            fontWeight: 700,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "8px",
            boxShadow: "0 4px 12px rgba(59, 130, 246, 0.15)",
            outline: "none",
            transition: "background 0.2s ease",
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = "#2563eb";
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = "var(--color-accent-blue)";
          }}
        >
          <Download size={12} />
          <span>DOWNLOAD NOW</span>
        </button>

        {/* Command shortcut guide */}
        <div
          style={{
            fontSize: "9px",
            color: "var(--color-text-muted)",
            display: "flex",
            justifyContent: "center",
            gap: "4px",
            fontFamily: "var(--font-jetbrains-mono), monospace",
          }}
        >
          <span>Press</span>
          <kbd
            style={{
              background: "rgba(255, 255, 255, 0.05)",
              border: "1px solid var(--color-border)",
              borderRadius: "3px",
              padding: "0 4px",
              color: "var(--color-text-secondary)",
            }}
          >
            Ctrl K
          </kbd>
        </div>
      </div>
    </div>
  );
}
