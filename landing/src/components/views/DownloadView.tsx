"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { Download, Copy, Check, Terminal, Cpu } from "lucide-react";

export default function DownloadView() {
  const [copiedText, setCopiedText] = useState<string | null>(null);

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedText(id);
    setTimeout(() => {
      setCopiedText(null);
    }, 2000);
  };

  const dnfCommand = "sudo dnf install ./trackora-2.1.0.rpm";
  const sourceCommands = "git clone https://github.com/SamXop123/Trackora.git\ncd Trackora\n./install.sh";

  return (
    <div
      style={{
        flex: 1,
        height: "100%",
        display: "flex",
        flexDirection: "column",
        padding: "32px",
        gap: "24px",
        justifyContent: "center",
        background: "rgba(10, 15, 24, 0.4)",
        overflow: "hidden",
      }}
    >
      {/* Header Title */}
      <div style={{ textAlign: "center", display: "flex", flexDirection: "column", gap: "6px", alignItems: "center" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <Download size={16} style={{ color: "var(--color-accent-blue)" }} />
          <span style={{ fontSize: "11px", fontWeight: 800, letterSpacing: "0.1em", color: "var(--color-text-secondary)" }}>
            GET STARTED WITH TRACKORA
          </span>
        </div>
        <h2 style={{ fontSize: "28px", fontWeight: 800, color: "var(--color-text-primary)", margin: 0 }}>
          Choose your platform
        </h2>
      </div>

      {/* Dual Equal Priority Cards Container */}
      <div
        style={{
          display: "flex",
          width: "100%",
          maxWidth: "820px",
          margin: "0 auto",
          gap: "20px",
          alignItems: "stretch",
          justifyContent: "center",
        }}
      >
        {/* Linux Card */}
        <motion.div
          whileHover={{ scale: 1.01 }}
          className="glass"
          style={{
            flex: 1,
            maxWidth: "390px",
            borderRadius: "14px",
            padding: "20px 22px",
            display: "flex",
            flexDirection: "column",
            gap: "14px",
            border: "1px solid rgba(59, 130, 246, 0.2)",
            background: "rgba(10, 15, 24, 0.8)",
            boxShadow: "0 20px 40px rgba(0, 0, 0, 0.4)",
            textAlign: "left",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid var(--color-border)", paddingBottom: "8px" }}>
            <span style={{ fontSize: "11px", fontWeight: 700, color: "var(--color-text-primary)", fontFamily: "var(--font-jetbrains-mono), monospace" }}>
              LINUX (GNOME WAYLAND)
            </span>
            <span style={{ fontSize: "10px", fontWeight: 700, color: "var(--color-accent-green)", fontFamily: "var(--font-jetbrains-mono), monospace" }}>
              STABLE
            </span>
          </div>

          {/* Linux Primary Download Button */}
          <motion.a
            href="/trackora-2.1.0.rpm"
            download
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "8px",
              background: "var(--color-accent-blue)",
              border: "1px solid rgba(59, 130, 246, 0.3)",
              color: "#ffffff",
              padding: "10px 18px",
              borderRadius: "8px",
              cursor: "pointer",
              fontSize: "12px",
              fontWeight: 700,
              letterSpacing: "0.03em",
              boxShadow: "0 4px 16px rgba(59, 130, 246, 0.2)",
              outline: "none",
              textDecoration: "none",
              transition: "background 0.2s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "#2563eb";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "var(--color-accent-blue)";
            }}
          >
            <Download size={14} />
            <span>DOWNLOAD FOR LINUX</span>
          </motion.a>

          {/* DNF Command */}
          <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
            <div style={{ fontSize: "10px", fontWeight: 700, color: "var(--color-text-secondary)" }}>
              FEDORA INSTALL (DNF)
            </div>
            <div
              style={{
                background: "rgba(5, 7, 10, 0.6)",
                borderRadius: "6px",
                padding: "8px 10px",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                fontFamily: "var(--font-jetbrains-mono), monospace",
                fontSize: "10.5px",
                color: "var(--color-text-primary)",
              }}
            >
              <span>{dnfCommand}</span>
              <button
                onClick={() => copyToClipboard(dnfCommand, "dnf")}
                style={{
                  background: "transparent",
                  border: "none",
                  color: copiedText === "dnf" ? "var(--color-accent-green)" : "var(--color-text-secondary)",
                  cursor: "pointer",
                  outline: "none",
                }}
              >
                {copiedText === "dnf" ? <Check size={14} /> : <Copy size={14} />}
              </button>
            </div>
          </div>

          {/* Source Build Command */}
          <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
            <div style={{ fontSize: "10px", fontWeight: 700, color: "var(--color-text-secondary)" }}>
              BUILD FROM SOURCE
            </div>
            <div
              style={{
                background: "rgba(5, 7, 10, 0.6)",
                borderRadius: "6px",
                padding: "8px 10px",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "flex-start",
                fontFamily: "var(--font-jetbrains-mono), monospace",
                fontSize: "10.5px",
                color: "var(--color-text-primary)",
              }}
            >
              <pre style={{ margin: 0, textAlign: "left", lineHeight: "1.3" }}>
                {sourceCommands}
              </pre>
              <button
                onClick={() => copyToClipboard(sourceCommands, "source")}
                style={{
                  background: "transparent",
                  border: "none",
                  color: copiedText === "source" ? "var(--color-accent-green)" : "var(--color-text-secondary)",
                  cursor: "pointer",
                  outline: "none",
                  marginTop: "2px",
                }}
              >
                {copiedText === "source" ? <Check size={14} /> : <Copy size={14} />}
              </button>
            </div>
          </div>

          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              fontSize: "10px",
              color: "var(--color-text-muted)",
              fontFamily: "var(--font-jetbrains-mono), monospace",
              borderTop: "1px solid var(--color-border)",
              paddingTop: "8px",
              marginTop: "auto",
            }}
          >
            <Terminal size={12} style={{ color: "var(--color-accent-blue)" }} />
            <span>LINUX GNOME DESKTOP</span>
          </div>
        </motion.div>

        {/* Windows Card */}
        <motion.div
          whileHover={{ scale: 1.01 }}
          className="glass"
          style={{
            flex: 1,
            maxWidth: "390px",
            borderRadius: "14px",
            padding: "20px 22px",
            display: "flex",
            flexDirection: "column",
            gap: "14px",
            border: "1px solid rgba(59, 130, 246, 0.2)",
            background: "rgba(10, 15, 24, 0.8)",
            boxShadow: "0 20px 40px rgba(0, 0, 0, 0.4)",
            textAlign: "left",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid var(--color-border)", paddingBottom: "8px" }}>
            <span style={{ fontSize: "11px", fontWeight: 700, color: "var(--color-text-primary)", fontFamily: "var(--font-jetbrains-mono), monospace" }}>
              WINDOWS (10 / 11)
            </span>
            <span style={{ fontSize: "10px", fontWeight: 700, color: "var(--color-accent-green)", fontFamily: "var(--font-jetbrains-mono), monospace" }}>
              STABLE
            </span>
          </div>

          {/* Windows Download Button */}
          <motion.a
            href="/TrackoraSetup-2.1.0.exe"
            download
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "8px",
              background: "var(--color-accent-blue)",
              border: "1px solid rgba(59, 130, 246, 0.3)",
              color: "#ffffff",
              padding: "10px 18px",
              borderRadius: "8px",
              cursor: "pointer",
              fontSize: "12px",
              fontWeight: 700,
              letterSpacing: "0.03em",
              boxShadow: "0 4px 16px rgba(59, 130, 246, 0.2)",
              outline: "none",
              textDecoration: "none",
              transition: "background 0.2s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "#2563eb";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "var(--color-accent-blue)";
            }}
          >
            <Download size={14} />
            <span>DOWNLOAD FOR WINDOWS</span>
          </motion.a>

          {/* Windows Features List */}
          <div
            style={{
              background: "rgba(5, 7, 10, 0.6)",
              borderRadius: "6px",
              padding: "10px 12px",
              display: "flex",
              flexDirection: "column",
              gap: "8px",
              fontSize: "11px",
              color: "var(--color-text-secondary)",
              lineHeight: "1.4",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <Cpu size={14} style={{ color: "var(--color-accent-blue)" }} />
              <span>Automatic background screen time & app focus tracking</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <Terminal size={14} style={{ color: "var(--color-accent-green)" }} />
              <span>System tray minimize & optional startup autostart setting</span>
            </div>
          </div>

          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "6px",
              fontSize: "10px",
              color: "var(--color-text-muted)",
              fontFamily: "var(--font-jetbrains-mono), monospace",
              borderTop: "1px solid var(--color-border)",
              paddingTop: "8px",
              marginTop: "auto",
            }}
          >
            <Cpu size={12} style={{ color: "var(--color-accent-blue)" }} />
            <span>WINDOWS 10 & 11 SUPPORTED</span>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
