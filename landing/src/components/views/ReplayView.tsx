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

export default function ReplayView({ onComplete }: ReplayViewProps) {
  const [stepIndex, setStepIndex] = useState(0);
  const [showConclusion, setShowConclusion] = useState(false);

  const nextStep = () => {
    if (stepIndex < REPLAY_STEPS.length - 1) {
      setStepIndex((prev) => prev + 1);
    } else {
      setShowConclusion(true);
    }
  };

  const currentStep = REPLAY_STEPS[stepIndex];
  const StepIcon = currentStep.icon;

  return (
    <div style={{ width: "100%", height: "100%", position: "relative" }}>
      <AnimatePresence mode="wait">
        {!showConclusion ? (
          <motion.div
            key="replay-flow"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
            style={{
              width: "100%",
              height: "100%",
              display: "flex",
              padding: "40px",
              gap: "40px",
              alignItems: "center",
              justifyContent: "space-between",
              background: "rgba(10, 15, 24, 0.4)",
              overflow: "hidden",
            }}
          >
            {/* Left pane: Active Step Detail */}
            <div
              style={{
                width: "50%",
                display: "flex",
                flexDirection: "column",
                gap: "20px",
                textAlign: "left",
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                <span
                  style={{
                    fontSize: "12px",
                    fontWeight: 800,
                    color: "var(--color-accent-blue)",
                    letterSpacing: "0.1em",
                    fontFamily: "var(--font-jetbrains-mono), monospace",
                  }}
                >
                  WHAT HAPPENED DURING YOUR DAY?
                </span>
                <span style={{ color: "var(--color-text-muted)" }}>•</span>
                <span
                  style={{
                    fontSize: "10px",
                    fontFamily: "var(--font-jetbrains-mono), monospace",
                    color: "var(--color-text-muted)",
                  }}
                >
                  STEP {stepIndex + 1} OF {REPLAY_STEPS.length}
                </span>
              </div>
    </div>
  );
}
