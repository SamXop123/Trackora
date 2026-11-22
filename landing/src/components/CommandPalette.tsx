"use client";

import React, { useEffect, useState, useRef, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Terminal, CornerDownLeft, Sparkles, Sun, Moon } from "lucide-react";
import { useTheme } from "../context/ThemeContext";

interface CommandPaletteProps {
  onNavigate: (view: string) => void;
  onToggleWarp?: () => void;
}

const COMMANDS = [
  { id: "intro", label: "Jump to Start (Intro)", shortcut: "1" },
  { id: "replay", label: "Replay Day", shortcut: "2" },
  { id: "dashboard", label: "View Habits Dashboard", shortcut: "3" },
  { id: "pipeline", label: "Inside Trackora", shortcut: "4" },
  { id: "privacy", label: "Inspect Privacy Controls", shortcut: "5" },
  { id: "download", label: "Jump to Get Started", shortcut: "6" },
  { id: "theme", label: "Toggle Theme (Light / Dark)", shortcut: "T" },
  { id: "warp", label: "Toggle Cosmic Warp Effect", shortcut: "W" },
];

export default function CommandPalette({ onNavigate, onToggleWarp }: CommandPaletteProps) {
  const { theme, toggleTheme } = useTheme();
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  const filteredCommands = useMemo(
    () => COMMANDS.filter((cmd) => cmd.label.toLowerCase().includes(search.toLowerCase())),
    [search]
  );

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Toggle Ctrl+K or Cmd+K
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setIsOpen((prev) => !prev);
      }

      // Close on Esc
      if (e.key === "Escape") {
        setIsOpen(false);
      }

      // Quick numbers navigation inside palette
      if (isOpen) {
        if (e.key >= "1" && e.key <= "6") {
          const idx = parseInt(e.key) - 1;
          e.preventDefault();
          onNavigate(COMMANDS[idx].id);
          setIsOpen(false);
        }

        if (e.key.toLowerCase() === "t") {
          e.preventDefault();
          toggleTheme();
          setIsOpen(false);
        }

        if (e.key.toLowerCase() === "w" && onToggleWarp) {
          e.preventDefault();
          onToggleWarp();
          setIsOpen(false);
        }

        // Navigation
        if (e.key === "ArrowDown") {
          e.preventDefault();
          setSelectedIndex((prev) => (filteredCommands.length > 0 ? (prev + 1) % filteredCommands.length : 0));
        }
        if (e.key === "ArrowUp") {
          e.preventDefault();
          setSelectedIndex((prev) => (filteredCommands.length > 0 ? (prev - 1 + filteredCommands.length) % filteredCommands.length : 0));
        }
        if (e.key === "Enter") {
          e.preventDefault();
          const cmd = filteredCommands[selectedIndex];
          if (cmd) {
            if (cmd.id === "theme") {
              toggleTheme();
            } else if (cmd.id === "warp" && onToggleWarp) {
              onToggleWarp();
            } else {
              onNavigate(cmd.id);
            }
            setIsOpen(false);
          }
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, selectedIndex, onNavigate, onToggleWarp, toggleTheme, filteredCommands]);

  // Click outside to close
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [isOpen]);

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            width: "100vw",
            height: "100vh",
            zIndex: 99999,
            background: "var(--color-palette-overlay)",
            backdropFilter: "blur(8px)",
            WebkitBackdropFilter: "blur(8px)",
            display: "flex",
            justifyContent: "center",
            alignItems: "flex-start",
            paddingTop: "140px",
          }}
        >
          <motion.div
            ref={containerRef}
            initial={{ scale: 0.96, y: -10 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.96, y: -10 }}
            transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
            className="glass"
            style={{
              width: "100%",
              maxWidth: "500px",
              borderRadius: "14px",
              boxShadow: "var(--color-modal-shadow)",
              overflow: "hidden",
            }}
          >
            {/* Input bar */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "12px",
                padding: "16px 20px",
                borderBottom: "1px solid var(--color-border)",
              }}
            >
              <Terminal size={18} style={{ color: "var(--color-accent-blue)" }} />
              <input
                type="text"
                autoFocus
                placeholder="Search commands or press shortcut key..."
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setSelectedIndex(0);
                }}
                style={{
                  flex: 1,
                  background: "transparent",
                  border: "none",
                  outline: "none",
                  color: "var(--color-text-primary)",
                  fontSize: "13px",
                  fontFamily: "var(--font-jetbrains-mono), monospace",
                }}
              />
              <span
                style={{
                  fontSize: "9px",
                  color: "var(--color-text-muted)",
                  fontFamily: "var(--font-jetbrains-mono), monospace",
                }}
              >
                ESC TO CLOSE
              </span>
            </div>

            {/* Commands list */}
            <div style={{ maxHeight: "300px", overflowY: "auto", padding: "8px" }}>
              {filteredCommands.length > 0 ? (
                filteredCommands.map((cmd, idx) => {
                  const isSelected = idx === selectedIndex;
                  return (
                    <div
                      key={cmd.id}
                      onClick={() => {
                        if (cmd.id === "theme") {
                          toggleTheme();
                        } else if (cmd.id === "warp" && onToggleWarp) {
                          onToggleWarp();
                        } else {
                          onNavigate(cmd.id);
                        }
                        setIsOpen(false);
                      }}
                      onMouseEnter={() => setSelectedIndex(idx)}
                      style={{
                        padding: "12px 16px",
                        borderRadius: "8px",
                        background: isSelected ? "var(--color-surface-hover)" : "transparent",
                        border: isSelected ? "1px solid var(--color-border)" : "1px solid transparent",
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        cursor: "pointer",
                        transition: "background 0.1s ease",
                      }}
                    >
                      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                        {cmd.id === "warp" ? (
                          <Sparkles size={14} style={{ color: "var(--color-accent-green)" }} />
                        ) : cmd.id === "theme" ? (
                          theme === "dark" ? (
                            <Sun size={14} style={{ color: "#fbbf24" }} />
                          ) : (
                            <Moon size={14} style={{ color: "var(--color-accent-blue)" }} />
                          )
                        ) : (
                          <Terminal size={14} style={{ color: "var(--color-text-secondary)" }} />
                        )}
                        <span style={{ fontSize: "12px", fontWeight: isSelected ? 600 : 500, color: isSelected ? "var(--color-text-primary)" : "var(--color-text-secondary)" }}>
                          {cmd.label}
                        </span>
                      </div>
                      
                      {/* Shortcut hint */}
                      <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                        <span
                          style={{
                            fontSize: "9px",
                            fontFamily: "var(--font-jetbrains-mono), monospace",
                            background: isSelected ? "rgba(var(--color-accent-blue-rgb), 0.15)" : "var(--color-surface-hover)",
                            border: isSelected ? "1px solid rgba(var(--color-accent-blue-rgb), 0.3)" : "1px solid var(--color-border)",
                            color: isSelected ? "var(--color-accent-blue)" : "var(--color-text-muted)",
                            borderRadius: "4px",
                            padding: "2px 6px",
                          }}
                        >
                          {cmd.shortcut}
                        </span>
                        {isSelected && <CornerDownLeft size={10} style={{ color: "var(--color-text-muted)" }} />}
                      </div>
                    </div>
                  );
                })
              ) : (
                <div style={{ padding: "20px", textAlign: "center", fontSize: "12px", color: "var(--color-text-muted)" }}>
                  No commands found matching &quot;{search}&quot;
                </div>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
