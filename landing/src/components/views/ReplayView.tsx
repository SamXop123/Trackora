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

              {/* Big time code */}
              <div style={{ display: "flex", alignItems: "baseline", gap: "16px" }}>
                <motion.h1
                  key={currentStep.time}
                  initial={{ opacity: 0, x: -15 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
                  style={{
                    fontSize: "92px",
                    fontWeight: 800,
                    letterSpacing: "-0.05em",
                    color: "var(--color-text-primary)",
                    lineHeight: "0.9",
                  }}
                >
                  {currentStep.time}
                </motion.h1>
                
                <motion.div
                  key={currentStep.app}
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.5 }}
                  style={{
                    padding: "6px 12px",
                    borderRadius: "20px",
                    background: `rgba(${currentStep.color === "#3b82f6" ? "59, 130, 246" : "156, 163, 175"}, 0.1)`,
                    border: `1px solid ${currentStep.color}33`,
                    color: currentStep.color,
                    fontSize: "11px",
                    fontWeight: 700,
                    display: "flex",
                    alignItems: "center",
                    gap: "6px",
                    fontFamily: "var(--font-jetbrains-mono), monospace",
                  }}
                >
                  <StepIcon size={12} />
                  <span>{currentStep.app.toUpperCase()}</span>
                </motion.div>
              </div>

              {/* Description log text */}
              <div style={{ height: "80px", display: "flex", flexDirection: "column", gap: "8px" }}>
                <AnimatePresence mode="wait">
                  <motion.div
                    key={currentStep.title}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.4 }}
                  >
                    <div
                      style={{
                        fontSize: "14px",
                        color: "var(--color-text-primary)",
                        fontWeight: 600,
                        fontFamily: "var(--font-jetbrains-mono), monospace",
                        whiteSpace: "nowrap",
                        textOverflow: "ellipsis",
                        overflow: "hidden",
                        maxWidth: "420px",
                      }}
                    >
                      {currentStep.title}
                    </div>
                    <div style={{ fontSize: "12px", color: "var(--color-text-secondary)", marginTop: "6px", lineHeight: "1.5" }}>
                      {currentStep.desc}
                    </div>
                  </motion.div>
                </AnimatePresence>
              </div>

              {/* Navigation Step Button */}
              <div>
                <motion.button
                  onClick={nextStep}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  style={{
                    background: stepIndex === REPLAY_STEPS.length - 1 ? "var(--color-accent-blue)" : "rgba(255, 255, 255, 0.03)",
                    border: "1px solid var(--color-border)",
                    borderColor: stepIndex === REPLAY_STEPS.length - 1 ? "rgba(59, 130, 246, 0.4)" : "var(--color-border)",
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
                    transition: "border-color 0.2s ease, background 0.2s ease",
                  }}
                >
                  <span>{stepIndex === REPLAY_STEPS.length - 1 ? "FINISH THE DAY" : "RELIVE THE MOMENT"}</span>
                  <ArrowRight size={12} />
                </motion.button>
              </div>
            </div>

            {/* Right pane: Chronological Wire Graph */}
            <div
              style={{
                width: "45%",
                height: "100%",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                position: "relative",
              }}
            >
              {/* Continuous wire line */}
              <div
                style={{
                  position: "absolute",
                  left: "50%",
                  top: "10%",
                  bottom: "10%",
                  width: "2px",
                  background: "rgba(255, 255, 255, 0.03)",
                  transform: "translateX(-50%)",
                  zIndex: 1,
                }}
              />

              {/* Scrolling progress wire line */}
              <motion.div
                animate={{ height: `${(stepIndex / (REPLAY_STEPS.length - 1)) * 80}%` }}
                transition={{ duration: 0.5, ease: "easeInOut" }}
                style={{
                  position: "absolute",
                  left: "50%",
                  top: "10%",
                  width: "2px",
                  background: "linear-gradient(to bottom, #1d4ed8, #3b82f6)",
                  boxShadow: "0 0 10px rgba(59, 130, 246, 0.5)",
                  transform: "translateX(-50%)",
                  zIndex: 2,
                  transformOrigin: "top",
                }}
              />

              {/* Timeline icons stack */}
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                  height: "80%",
                  position: "relative",
                  zIndex: 3,
                  width: "100%",
                }}
              >
                {REPLAY_STEPS.map((step, idx) => {
                  const Icon = step.icon;
                  const isPassed = idx <= stepIndex;
                  const isCurrent = idx === stepIndex;

                  return (
                    <div
                      key={idx}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        position: "relative",
                      }}
                    >
                      {/* Node icon button */}
                      <motion.div
                        animate={{
                          scale: isCurrent ? 1.25 : 1,
                          backgroundColor: isCurrent 
                            ? step.color 
                            : isPassed 
                              ? "rgba(59, 130, 246, 0.15)" 
                              : "#0a0f18",
                          borderColor: isCurrent 
                            ? "#ffffff" 
                            : isPassed 
                              ? step.color 
                              : "var(--color-border)",
                          boxShadow: isCurrent 
                            ? `0 0 20px ${step.color}` 
                            : "none",
                        }}
                        transition={{ duration: 0.3 }}
                        style={{
                          width: "36px",
                          height: "36px",
                          borderRadius: "50%",
                          border: "2px solid",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          cursor: "pointer",
                          color: isCurrent ? "#ffffff" : isPassed ? step.color : "var(--color-text-muted)",
                        }}
                        onClick={() => setStepIndex(idx)}
                      >
                        <Icon size={14} />
                      </motion.div>

                      {/* Micro time indicator on the right */}
                      <div
                        style={{
                          position: "absolute",
                          left: "calc(50% + 28px)",
                          fontSize: "10px",
                          fontWeight: isCurrent ? 700 : 500,
                          color: isCurrent ? "var(--color-text-primary)" : "var(--color-text-muted)",
                          fontFamily: "var(--font-jetbrains-mono), monospace",
                        }}
                      >
                        {step.time}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </motion.div>
        ) : (
                }}
              >
                <span>SEE YOUR HABITS</span>
                <ArrowRight size={14} />
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
