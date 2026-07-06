"use client";

import React, { useEffect, useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Terminal, CornerDownLeft, Sparkles } from "lucide-react";

interface CommandPaletteProps {
  onNavigate: (view: string) => void;
  onToggleWarp?: () => void;
}

const COMMANDS = [
  { id: "intro", label: "Jump to Start (Intro)", shortcut: "1" },
  { id: "replay", label: "Replay Day", shortcut: "2" },
  { id: "dashboard", label: "View Habits Dashboard", shortcut: "3" },
  { id: "pipeline", label: "Inspect Inside Trackora", shortcut: "4" },
  { id: "privacy", label: "Inspect Privacy Controls", shortcut: "5" },
  { id: "download", label: "Jump to Get Started", shortcut: "6" },
  { id: "warp", label: "Toggle Cosmic Warp Effect", shortcut: "W" },
];

export default function CommandPalette({ onNavigate, onToggleWarp }: CommandPaletteProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

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

        if (e.key.toLowerCase() === "w" && onToggleWarp) {
          e.preventDefault();
          onToggleWarp();
          setIsOpen(false);
        }

        // Navigation
        if (e.key === "ArrowDown") {
          e.preventDefault();
          setSelectedIndex((prev) => (prev + 1) % filteredCommands.length);
        }
        if (e.key === "ArrowUp") {
          e.preventDefault();
          setSelectedIndex((prev) => (prev - 1 + filteredCommands.length) % filteredCommands.length);
        }
        if (e.key === "Enter") {
          e.preventDefault();
          const cmd = filteredCommands[selectedIndex];
          if (cmd) {
            if (cmd.id === "warp" && onToggleWarp) {
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
  }, [isOpen, selectedIndex, onNavigate, onToggleWarp]);

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

  const filteredCommands = COMMANDS.filter((cmd) =>
    cmd.label.toLowerCase().includes(search.toLowerCase())
  );

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
            background: "rgba(3, 5, 8, 0.6)",
            backdropFilter: "blur(8px)",
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
              boxShadow: "0 40px 80px rgba(0, 0, 0, 0.7), 0 0 0 1px rgba(255, 255, 255, 0.05)",
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
            <div style={{ maxHeight: "280px", overflowY: "auto", padding: "8px" }}>
              {filteredCommands.length > 0 ? (
                filteredCommands.map((cmd, idx) => {
                  const isSelected = idx === selectedIndex;
                  return (
                    <div
                      key={cmd.id}
                      onClick={() => {
                        if (cmd.id === "warp" && onToggleWarp) {
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
                        background: isSelected ? "rgba(255, 255, 255, 0.03)" : "transparent",
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
                            background: isSelected ? "rgba(59, 130, 246, 0.15)" : "rgba(255, 255, 255, 0.05)",
                            border: isSelected ? "1px solid rgba(59, 130, 246, 0.3)" : "1px solid var(--color-border)",
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
                  No commands found matching "{search}"
                </div>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
