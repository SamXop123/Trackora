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

  const dnfCommand = "sudo dnf install ./trackora-v1.rpm";
  const sourceCommands = "git clone https://github.com/SamXop123/Trackora.git\ncd Trackora\n./install.sh";

  return (
    <div
      style={{
        flex: 1,
        height: "100%",
        display: "flex",
        padding: "32px",
        gap: "24px",
        alignItems: "center",
        justifyContent: "space-between",
        background: "rgba(10, 15, 24, 0.4)",
        overflow: "hidden",
      }}
    >
      {/* Left panel: Linux Release DNF / Source installation */}
      <div
        style={{
          width: "52%",
          display: "flex",
          flexDirection: "column",
          gap: "20px",
          textAlign: "left",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <Download size={16} style={{ color: "var(--color-accent-blue)" }} />
          <span style={{ fontSize: "11px", fontWeight: 800, letterSpacing: "0.1em", color: "var(--color-text-secondary)" }}>
            HOW DO I START?
          </span>
        </div>

        <div>
          <span
            style={{
              fontSize: "10px",
              fontFamily: "var(--font-jetbrains-mono), monospace",
              color: "var(--color-accent-green)",
              fontWeight: 700,
              background: "rgba(16, 185, 129, 0.08)",
              padding: "4px 8px",
              borderRadius: "6px",
              border: "1px solid rgba(16, 185, 129, 0.2)",
            }}
          >
            v1.0 STABLE
          </span>
          <h2
            style={{
              fontSize: "30px",
              fontWeight: 800,
              color: "var(--color-text-primary)",
              marginTop: "12px",
              lineHeight: "1.1",
            }}
          >
            Start knowing. Today.
          </h2>
        </div>

        {/* Direct RPM Download Button */}
        <div style={{ margin: "4px 0" }}>
          <motion.a
            href="/trackora-v1.rpm"
            download
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "10px",
              background: "var(--color-accent-blue)",
              border: "1px solid rgba(59, 130, 246, 0.3)",
              color: "#ffffff",
              padding: "12px 24px",
              borderRadius: "8px",
              cursor: "pointer",
              fontSize: "12px",
              fontWeight: 700,
              letterSpacing: "0.05em",
              boxShadow: "0 4px 20px rgba(59, 130, 246, 0.2)",
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
            <span>DOWNLOAD NATIVE RPM (v1.0)</span>
          </motion.a>
        </div>

        {/* Option A: DNF installation */}
        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          <div style={{ fontSize: "10px", fontWeight: 700, color: "var(--color-text-secondary)" }}>
            DNF INSTALL (FEDORA LINUX)
          </div>
          
          <div
            className="glass"
            style={{
              background: "rgba(5, 7, 10, 0.6)",
              borderRadius: "8px",
              padding: "10px 14px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              fontFamily: "var(--font-jetbrains-mono), monospace",
              fontSize: "11px",
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

        {/* Option B: Source installation */}
        <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
          <div style={{ fontSize: "10px", fontWeight: 700, color: "var(--color-text-secondary)" }}>
            BUILD FROM SOURCE (ANY COMPOSITOR)
          </div>

          <div
            className="glass"
            style={{
              background: "rgba(5, 7, 10, 0.6)",
              borderRadius: "8px",
              padding: "10px 14px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "flex-start",
              fontFamily: "var(--font-jetbrains-mono), monospace",
              fontSize: "11px",
              color: "var(--color-text-primary)",
            }}
          >
            <pre style={{ margin: 0, textAlign: "left", lineHeight: "1.4" }}>
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
      </div>

      {/* Right panel: Windows Support Card */}
      <div
        style={{
          width: "44%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        <motion.div
          whileHover={{ scale: 1.03 }}
          className="glass"
          style={{
            width: "100%",
            maxWidth: "280px",
            borderRadius: "14px",
            padding: "20px",
            display: "flex",
            flexDirection: "column",
            gap: "16px",
            boxShadow: "0 20px 40px rgba(0, 0, 0, 0.4)",
            border: "1px solid rgba(59, 130, 246, 0.15)",
            background: "rgba(10, 15, 24, 0.8)",
          }}
        >
          {/* Mock Windows Header */}
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid var(--color-border)", paddingBottom: "10px" }}>
            <span style={{ fontSize: "10px", fontWeight: 700, color: "var(--color-text-secondary)", fontFamily: "var(--font-jetbrains-mono), monospace" }}>
              COMING NEXT
            </span>
            <div style={{ display: "flex", gap: "6px" }}>
              <div style={{ width: "8px", height: "1px", background: "var(--color-text-muted)" }} />
              <div style={{ width: "8px", height: "8px", border: "1px solid var(--color-text-muted)" }} />
              <div style={{ width: "8px", height: "8px", background: "var(--color-text-muted)" }} />
            </div>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: "8px", textAlign: "left" }}>
            <div
              style={{
                fontSize: "9px",
                fontFamily: "var(--font-jetbrains-mono), monospace",
                color: "var(--color-accent-blue)",
                fontWeight: 700,
                background: "rgba(59, 130, 246, 0.08)",
                padding: "3px 6px",
                borderRadius: "4px",
                width: "fit-content",
              }}
            >
              IN DEVELOPMENT
            </div>
            <h3 style={{ fontSize: "16px", color: "var(--color-text-primary)" }}>
              Windows Support
            </h3>
            <p style={{ fontSize: "11px", color: "var(--color-text-secondary)", lineHeight: "1.4" }}>
              Track hours, focus, and habits natively on Windows. Launching in version 2.0.
            </p>
          </div>

          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "8px",
              fontSize: "10px",
              color: "var(--color-text-muted)",
              fontFamily: "var(--font-jetbrains-mono), monospace",
              borderTop: "1px solid var(--color-border)",
              paddingTop: "12px",
            }}
          >
            <Cpu size={12} style={{ color: "var(--color-accent-blue)" }} />
            <span>X64 & ARM64 SUPPORT</span>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
