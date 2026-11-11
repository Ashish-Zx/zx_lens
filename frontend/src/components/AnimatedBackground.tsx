"use client";

import { motion } from "framer-motion";

interface Orb {
  size: number;
  left: string;
  top: string;
  background: string;
  duration: number;
}

// Ambient gradient orbs that drift slowly behind the glass UI.
// Colors are theme-agnostic translucent hues; they glow softly on any bg.
const ORBS: Orb[] = [
  { size: 440, left: "-8%", top: "-18%", background: "rgba(124,58,237,0.32)", duration: 20 },
  { size: 360, left: "72%", top: "-12%", background: "rgba(99,102,241,0.28)", duration: 24 },
  { size: 340, left: "82%", top: "58%", background: "rgba(168,85,247,0.22)", duration: 28 },
  { size: 400, left: "-6%", top: "55%", background: "rgba(56,189,248,0.20)", duration: 22 },
];

export function AnimatedBackground() {
  return (
    <div aria-hidden className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      {ORBS.map((orb, i) => (
        <motion.div
          key={i}
          className="absolute rounded-full blur-3xl"
          style={{
            width: orb.size,
            height: orb.size,
            left: orb.left,
            top: orb.top,
            background: orb.background,
          }}
          animate={{ x: [0, 48, -24, 0], y: [0, -40, 24, 0], scale: [1, 1.15, 0.95, 1] }}
          transition={{ duration: orb.duration, repeat: Infinity, ease: "easeInOut" }}
        />
      ))}
    </div>
  );
}
