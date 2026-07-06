"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ShieldCheck, ArrowRight, ShieldAlert, CheckCircle, Database } from "lucide-react";

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
        background: "rgba(10, 15, 24, 0.2)",
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
            <span>GET STARTED</span>
            <ArrowRight size={12} style={{ color: "var(--color-accent-blue)" }} />
          </button>
        </div>
      </div>

      {/* Right panel: Database Cylinder & Click-Recovery Test */}
      <div
        style={{
