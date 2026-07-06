"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowRight, Code, Globe, Terminal, Music, MessageSquare } from "lucide-react";

interface ReplayViewProps {
  onComplete: () => void;
}

const REPLAY_STEPS = [
  {
    time: "09:02",
    app: "VS Code",
    title: "VS Code",
    icon: Code,
    color: "#3b82f6",
    desc: "Writing the first lines of code. The cursor flashes in anticipation.",
  },
  {
    time: "10:41",
    app: "Brave Browser",
    title: "Brave Browser",
    icon: Globe,
    color: "#f97316",
    desc: "Scanning documentation. Looking for that one missing detail.",
  },
  {
    time: "11:17",
    app: "Terminal",
    title: "Terminal",
    icon: Terminal,
    color: "#10b981",
    desc: "Deploying and watching logs roll by. Waiting for the build to pass.",
  },
  {
    time: "12:58",
    app: "Spotify",
    title: "Spotify",
    icon: Music,
    color: "#1db954",
    desc: "Putting on some beats. Taking a deep breath to reset focus.",
  },
  {
    time: "15:20",
    app: "VS Code",
    title: "VS Code",
    icon: Code,
    color: "#3b82f6",
    desc: "Flow state. Two hours slip away like minutes.",
  },
  {
    time: "17:45",
    app: "Discord",
    title: "Discord",
    icon: MessageSquare,
    color: "#5865f2",
    desc: "Syncing with the team. Winding down the day's milestones.",
  },
];

