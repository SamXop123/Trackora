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

