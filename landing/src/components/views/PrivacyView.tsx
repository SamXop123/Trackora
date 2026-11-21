"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { ShieldCheck, ArrowRight, CheckCircle, Database } from "lucide-react";

interface PrivacyViewProps {
  onComplete: () => void;
}

const PRIVACY_BULLETS = [
  { text: "NO ACCOUNT REQUIRED", desc: "No signup forms. No profiles. Trackora runs locally without logins." },
  { text: "ZERO TELEMETRY", desc: "No remote calls. We track nothing. What happens on your machine stays there." },
  { text: "LOCAL ONLY", desc: "Runs without internet access. Absolutely no cloud sync or remote databases." },
];

export default function PrivacyView({ onComplete }: PrivacyViewProps) {
  const [logs, setLogs] = useState<string[]>([]);
  const [isRecovering, setIsRecovering] = useState(false);

  const triggerRecovery = () => {
    if (isRecovering) return;
    setIsRecovering(true);
    setLogs([]);

    const recoveryLogs = [
      "vault: Verifying file database integrity...",
      "vault: Found 1 session unclosed from previous run.",
      "vault: [INFO] Session was left open due to sudden system shutdown.",
      "vault: Closing stale session safely at last recorded focus time.",
      "vault: Focus session recovered successfully. Total hours updated.",
      "vault: System clean. Ready to track.",
    ];

    let logIdx = 0;
    const printLog = () => {
      if (logIdx < recoveryLogs.length) {
        setLogs((prev) => [...prev, recoveryLogs[logIdx]]);
        logIdx++;
        setTimeout(printLog, 300);
      } else {
        setIsRecovering(false);
      }
    };
    printLog();
  };

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
        background: "var(--color-view-bg)",
        overflow: "hidden",
      }}
    >
      {/* Left panel: Bullet-proof copy */}
      <div
        style={{
          width: "48%",
          display: "flex",
          flexDirection: "column",
          gap: "24px",
          textAlign: "left",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <ShieldCheck size={16} style={{ color: "var(--color-accent-green)" }} />
          <span style={{ fontSize: "11px", fontWeight: 800, letterSpacing: "0.1em", color: "var(--color-text-secondary)" }}>
            WHO OWNS YOUR DATA?
          </span>
        </div>

        <div>
          <h2
            style={{
              fontSize: "32px",
              fontWeight: 800,
              color: "var(--color-text-primary)",
              lineHeight: "1.1",
            }}
          >
            Your attention is yours. <br />
            So is your data.
          </h2>
        </div>

        {/* Security checks grid */}
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {PRIVACY_BULLETS.map((bullet) => (
            <div key={bullet.text} style={{ display: "flex", gap: "12px", alignItems: "flex-start" }}>
              <CheckCircle size={14} style={{ color: "var(--color-accent-green)", marginTop: "3px" }} />
              <div>
                <div style={{ fontSize: "11px", fontWeight: 700, color: "var(--color-text-primary)" }}>
                  {bullet.text}
                </div>
                <div style={{ fontSize: "11px", color: "var(--color-text-secondary)", marginTop: "2px" }}>
                  {bullet.desc}
                </div>
              </div>
            </div>
          ))}
        </div>

        <div>
          <button
            onClick={onComplete}
            style={{
              background: "var(--color-surface-hover)",
              border: "1px solid var(--color-border)",
              color: "var(--color-text-primary)",
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
            <span>GET STARTED</span>
            <ArrowRight size={12} style={{ color: "var(--color-accent-blue)" }} />
          </button>
        </div>
      </div>

      {/* Right panel: Database Cylinder & Click-Recovery Test */}
      <div
        style={{
          width: "48%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: "20px",
          position: "relative",
        }}
      >
        {/* Floating security rings */}
        <div
          style={{
            position: "absolute",
            width: "280px",
            height: "280px",
            borderRadius: "50%",
            border: "1px dashed rgba(var(--color-accent-green-rgb), 0.15)",
            pointerEvents: "none",
          }}
        />

        {/* Database cylinder button */}
        <motion.button
          onClick={triggerRecovery}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.98 }}
          style={{
            width: "120px",
            height: "120px",
            borderRadius: "50%",
            background: "radial-gradient(circle, rgba(var(--color-accent-green-rgb), 0.15) 0%, transparent 70%)",
            border: "2px solid rgba(var(--color-accent-green-rgb), 0.3)",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            gap: "8px",
            cursor: "pointer",
            outline: "none",
            boxShadow: "0 0 40px rgba(var(--color-accent-green-rgb), 0.12)",
          }}
        >
          <Database size={28} style={{ color: "var(--color-accent-green)" }} />
          <span style={{ fontSize: "9px", fontFamily: "var(--font-jetbrains-mono), monospace", color: "var(--color-accent-green)", fontWeight: 700 }}>
            {isRecovering ? "SIMULATING..." : "SECURE BOOT"}
          </span>
        </motion.button>

        {/* Recovery logs output box */}
        <div
          className="glass"
          style={{
            width: "300px",
            height: "130px",
            borderRadius: "10px",
            padding: "12px",
            display: "flex",
            flexDirection: "column",
            justifyContent: "flex-end",
            overflow: "hidden",
            background: "var(--color-code-bg)",
            border: "1px solid var(--color-border)",
          }}
        >
          {logs.length > 0 ? (
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "4px",
                fontSize: "9px",
                fontFamily: "var(--font-jetbrains-mono), monospace",
                textAlign: "left",
                color: "var(--color-text-secondary)",
              }}
            >
              {logs.slice(-5).map((log, idx) => (
                <div
                  key={idx}
                  style={{
                    color: log.includes("SUCCESS") || log.includes("Clean") || log.includes("clean")
                      ? "var(--color-accent-green)"
                      : log.includes("WARNING") || log.includes("INFO")
                        ? "var(--color-accent-blue)"
                        : "var(--color-text-secondary)",
                  }}
                >
                  {log}
                </div>
              ))}
            </div>
          ) : (
            <div style={{ fontSize: "10px", color: "var(--color-text-muted)", fontFamily: "var(--font-jetbrains-mono), monospace", textAlign: "center", paddingBottom: "36px" }}>
              Tap the database container above to simulate a secure offline boot sequence
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
