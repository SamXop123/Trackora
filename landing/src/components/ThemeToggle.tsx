"use client";

import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sun, Moon } from "lucide-react";
import { useTheme } from "../context/ThemeContext";

interface ThemeToggleProps {
  showLabel?: boolean;
  className?: string;
  size?: "sm" | "md";
}

export default function ThemeToggle({ showLabel = false, size = "sm" }: ThemeToggleProps) {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";

  return (
    <motion.button
      onClick={toggleTheme}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.94 }}
      type="button"
      aria-label={isDark ? "Switch to Light Theme" : "Switch to Dark Theme"}
      title={isDark ? "Switch to Light Theme" : "Switch to Dark Theme"}
      style={{
        background: "var(--color-surface-hover)",
        border: "1px solid var(--color-border)",
        color: isDark ? "var(--color-text-secondary)" : "var(--color-text-primary)",
        borderRadius: "8px",
        padding: showLabel ? "6px 12px" : size === "sm" ? "6px" : "8px",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        gap: "8px",
        cursor: "pointer",
        outline: "none",
        transition: "border-color 0.2s ease, background 0.2s ease, color 0.2s ease",
        fontFamily: "var(--font-jetbrains-mono), monospace",
        fontSize: "10px",
        fontWeight: 600,
        letterSpacing: "0.04em",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = "var(--color-accent-blue)";
        e.currentTarget.style.color = "var(--color-accent-blue)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = "var(--color-border)";
        e.currentTarget.style.color = isDark ? "var(--color-text-secondary)" : "var(--color-text-primary)";
      }}
    >
      <AnimatePresence mode="wait" initial={false}>
        <motion.div
          key={theme}
          initial={{ rotate: -90, opacity: 0, scale: 0.8 }}
          animate={{ rotate: 0, opacity: 1, scale: 1 }}
          exit={{ rotate: 90, opacity: 0, scale: 0.8 }}
          transition={{ duration: 0.2 }}
          style={{ display: "flex", alignItems: "center", justifyContent: "center" }}
        >
          {isDark ? (
            <Sun size={size === "sm" ? 14 : 16} strokeWidth={2} />
          ) : (
            <Moon size={size === "sm" ? 14 : 16} strokeWidth={2} />
          )}
        </motion.div>
      </AnimatePresence>

      {showLabel && (
        <span>{isDark ? "LIGHT THEME" : "DARK THEME"}</span>
      )}
    </motion.button>
  );
}
