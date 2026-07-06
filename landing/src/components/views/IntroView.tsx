"use client";

import React from "react";
import { motion } from "framer-motion";
import { ArrowRight, Download } from "lucide-react";

interface IntroViewProps {
  onStartReplay: () => void;
  onNavigateDownload: () => void;
}

export default function IntroView({ onStartReplay, onNavigateDownload }: IntroViewProps) {
  return (
    <div
      style={{
        flex: 1,
        height: "100%",
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        alignItems: "center",
        padding: "40px",
        background: "radial-gradient(circle at center, rgba(16, 24, 48, 0.2) 0%, rgba(5, 7, 10, 0) 70%)",
        position: "relative",
      }}
    >
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: "20px",
          textAlign: "center",
          maxWidth: "520px",
        }}
      >
        {/* Cinematic questioning typography in lowercase */}
        <motion.h1
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
          style={{
            fontSize: "48px",
            fontWeight: 800,
            color: "var(--color-text-primary)",
            lineHeight: "1.1",
            letterSpacing: "-0.04em",
          }}
        >
          where did today go?
        </motion.h1>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1.2, delay: 0.6 }}
          style={{
            fontSize: "24px",
            fontWeight: 500,
            color: "var(--color-accent-blue)",
            letterSpacing: "-0.02em",
          }}
        >
          trackora knows.
        </motion.p>

        {/* CTA Buttons Row */}
        <div style={{ display: "flex", gap: "16px", marginTop: "24px" }}>
          {/* Start Replay Button */}
          <motion.button
            onClick={onStartReplay}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 1, ease: [0.16, 1, 0.3, 1] }}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.98 }}
            style={{
              background: "rgba(255, 255, 255, 0.03)",
              border: "1px solid var(--color-border)",
              color: "var(--color-text-primary)",
              padding: "12px 24px",
              borderRadius: "30px",
              cursor: "pointer",
              fontSize: "12px",
              fontWeight: 700,
              letterSpacing: "0.05em",
              display: "flex",
              alignItems: "center",
              gap: "10px",
              boxShadow: "0 4px 20px rgba(0, 0, 0, 0.2)",
              outline: "none",
              transition: "border-color 0.2s ease, background 0.2s ease",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = "var(--color-accent-blue)";
              e.currentTarget.style.background = "rgba(59, 130, 246, 0.05)";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = "var(--color-border)";
              e.currentTarget.style.background = "rgba(255, 255, 255, 0.03)";
            }}
          >
            <span>REPLAY YOUR DAY</span>
            <ArrowRight size={14} style={{ color: "var(--color-accent-blue)" }} />
          </motion.button>

          {/* Linux RPM Download Button - Navigates to download view */}
          <motion.button
            onClick={onNavigateDownload}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.8, delay: 1.2, ease: [0.16, 1, 0.3, 1] }}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.98 }}
            style={{
              background: "var(--color-accent-blue)",
              border: "1px solid rgba(59, 130, 246, 0.3)",
              color: "#ffffff",
              padding: "12px 24px",
              borderRadius: "30px",
              cursor: "pointer",
              fontSize: "12px",
              fontWeight: 700,
              letterSpacing: "0.05em",
              display: "flex",
              alignItems: "center",
              gap: "10px",
              boxShadow: "0 4px 20px rgba(59, 130, 246, 0.25)",
              outline: "none",
              transition: "background 0.2s ease, box-shadow 0.2s ease",
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
          </motion.button>
        </div>
      </div>

      {/* Floating prompt info */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 1, delay: 1.6 }}
        style={{
          position: "absolute",
          bottom: "30px",
          fontSize: "10px",
          color: "var(--color-text-muted)",
          fontFamily: "var(--font-jetbrains-mono), monospace",
        }}
      >
        SCROLL OR USE THE SIDEBAR TO UNFOLD THE DAY
      </motion.div>
    </div>
  );
}
