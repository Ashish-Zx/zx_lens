"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  UploadCloud,
  Scissors,
  Database,
  Network,
  Gauge,
  Sparkles,
  MessageSquareText,
} from "lucide-react";

interface Step {
  title: string;
  tag: string;
  description: string;
  detail: string;
  icon: React.ElementType;
}

const STEPS: Step[] = [
  {
    title: "Upload & Parse",
    tag: "Ingestion",
    description: "Starts the moment you drop in a PDF.",
    detail:
      "Your file is parsed into structured content — text, tables, and section hierarchy — using Docling, so nothing meaningful is lost.",
    icon: UploadCloud,
  },
  {
    title: "Contextual Chunking",
    tag: "Preparation",
    description: "We split the document into intelligent pieces.",
    detail:
      "Content is split into overlapping chunks enriched with surrounding context, so each retrievable piece stands on its own.",
    icon: Scissors,
  },
  {
    title: "Embed & Index",
    tag: "Storage",
    description: "Every chunk becomes searchable instantly.",
    detail:
      "Dense embeddings land in a Chroma vector store, while BM25 builds a sparse keyword index — two complementary views of the same source.",
    icon: Database,
  },
  {
    title: "Hybrid Retrieval",
    tag: "Search",
    description: "Your question hunts across both indexes.",
    detail:
      "On ask, the query retrieves the most relevant chunks from dense + sparse signals, fused with Reciprocal Rank Fusion for balanced results.",
    icon: Network,
  },
  {
    title: "Rerank",
    tag: "Precision",
    description: "We re-sort candidates for accuracy.",
    detail:
      "A cross-encoder reranker scores the shortlist and reorders it, so the strongest evidence floats to the top.",
    icon: Gauge,
  },
  {
    title: "Grounded Generation",
    tag: "Synthesis",
    description: "The LLM writes from your sources only.",
    detail:
      "The generator answers strictly from the retrieved chunks, emitting an inline citation [n] for every claim it makes.",
    icon: Sparkles,
  },
  {
    title: "Cited Answer",
    tag: "Deliver",
    description: "You get verifiable, linked proof.",
    detail:
      "The final answer ships with a clickable source list — every citation maps back to the exact page and passage it came from.",
    icon: MessageSquareText,
  },
];

const CYCLE_MS = 2000;

export function PipelineFlow() {
  const [active, setActive] = useState(0);

  useEffect(() => {
    const id = setInterval(() => {
      setActive((a) => (a + 1) % STEPS.length);
    }, CYCLE_MS);
    return () => clearInterval(id);
  }, []);

  const step = STEPS[active];
  const progress = (active / (STEPS.length - 1)) * 100;
  const Icon = step.icon;

  return (
    <section className="mx-auto mt-20 max-w-5xl">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-80px" }}
        transition={{ duration: 0.5 }}
        className="text-center"
      >
        <span className="inline-flex items-center gap-2 rounded-full bg-accent-soft px-3 py-1 text-xs font-medium text-accent">
          <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-accent" />
          Behind the scenes
        </span>
        <h2 className="mt-4 text-2xl font-bold tracking-tight text-ink sm:text-3xl">
          How your answer actually gets built
        </h2>
        <p className="mx-auto mt-3 max-w-lg text-sm text-ink-faint">
          Every question runs through a seven-stage retrieval-augmented
          pipeline before you see a single word.
        </p>
      </motion.div>

      {/* Stepper */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-60px" }}
        transition={{ duration: 0.5, delay: 0.1 }}
        className="relative mt-12"
      >
        {/* connector track */}
        <div className="absolute inset-x-0 top-6 h-px bg-line" />
        {/* progress fill */}
        <motion.div
          className="absolute top-6 left-0 h-px bg-gradient-to-r from-accent to-accent-strong"
          animate={{ width: `${progress}%` }}
          transition={{ type: "spring", stiffness: 60, damping: 20 }}
        />
        {/* traveling dot */}
        <motion.div
          className="absolute top-6 z-10 h-3 w-3 -translate-y-1/2 rounded-full bg-accent shadow-glow"
          animate={{ left: `${progress}%` }}
          transition={{ type: "spring", stiffness: 60, damping: 20 }}
        />

        <div className="relative flex items-start justify-between">
          {STEPS.map((s, i) => {
            const NodeIcon = s.icon;
            const isActive = i === active;
            const isDone = i < active;
            return (
              <button
                key={i}
                type="button"
                onClick={() => setActive(i)}
                className="group flex w-[13%] flex-col items-center"
                aria-pressed={isActive}
              >
                <motion.div
                  animate={{
                    scale: isActive ? 1.12 : 1,
                    backgroundColor: isActive || isDone ? "var(--accent)" : "var(--surface)",
                    color: isActive || isDone ? "#fff" : "var(--text-secondary)",
                  }}
                  transition={{ type: "spring", stiffness: 260, damping: 20 }}
                  className="flex h-12 w-12 items-center justify-center rounded-2xl border border-line shadow-glow"
                >
                  <NodeIcon className="h-5 w-5" />
                </motion.div>
                <span className="mt-2 hidden text-center text-[10px] font-medium leading-tight text-ink-soft sm:block">
                  {s.title}
                </span>
              </button>
            );
          })}
        </div>
      </motion.div>

      {/* Active step detail */}
      <div className="glass mt-8 min-h-[150px] rounded-2xl p-6 sm:p-7">
        <AnimatePresence mode="wait">
          <motion.div
            key={active}
            initial={{ opacity: 0, x: 16 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -16 }}
            transition={{ duration: 0.3, ease: "easeOut" }}
          >
            <div className="flex items-center gap-3">
              <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-accent-soft">
                <Icon className="h-5 w-5 text-accent" />
              </span>
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-wider text-accent">
                  Step {active + 1} · {step.tag}
                </p>
                <h3 className="text-base font-semibold text-ink">{step.title}</h3>
              </div>
            </div>
            <p className="mt-3 text-xs font-medium text-ink-soft">
              {step.description}
            </p>
            <p className="mt-1.5 text-sm leading-relaxed text-ink-soft">
              {step.detail}
            </p>
          </motion.div>
        </AnimatePresence>
      </div>
    </section>
  );
}
