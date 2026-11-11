"use client";

import { useState } from "react";
import { Loader2, MessageCircleQuestion, Sparkles, TriangleAlert } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { RAGResponse } from "@/types";
import { MarkdownRenderer } from "./MarkdownRenderer";
import { CitationList } from "./CitationList";

interface AnswerPanelProps {
  response: RAGResponse | null;
  isLoading: boolean;
  error: string | null;
}

const bodyVariants = {
  initial: { opacity: 0, y: 10, scale: 0.97 },
  animate: { opacity: 1, y: 0, scale: 1 },
  exit: { opacity: 0, y: -8, scale: 0.97 },
};

const transition = { duration: 0.28, ease: "easeOut" as const };

export function AnswerPanel({ response, isLoading, error }: AnswerPanelProps) {
  const [activeCitationId, setActiveCitationId] = useState<number | null>(null);

  return (
    <section className="glass flex flex-col rounded-xl border border-line shadow-glow">
      <div className="flex items-center gap-2.5 border-b border-line px-4 py-3">
        <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-accent-soft">
          <Sparkles className="h-4 w-4 text-accent" />
        </span>
        <h2 className="text-sm font-semibold text-ink">Answer</h2>
        {response && !isLoading && (
          <span className="ml-auto inline-flex items-center rounded-full border border-line-strong bg-accent-soft px-2 py-0.5 text-[11px] font-medium text-accent">
            {(response.total_latency_ms / 1000).toFixed(1)}s
          </span>
        )}
      </div>

      <div className="flex-1 p-4 sm:p-5">
        <AnimatePresence mode="wait">
          {isLoading ? (
            <motion.div
              key="loading"
              variants={bodyVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              transition={transition}
              className="flex flex-col items-center justify-center gap-5 py-16"
            >
              <div className="relative flex h-14 w-14 items-center justify-center">
                <span className="absolute inset-0 rounded-full bg-accent-soft blur-md" />
                <Loader2 className="relative h-7 w-7 animate-spin text-accent" />
              </div>
              <div className="flex items-center gap-1.5 text-sm text-ink-soft">
                <span>Gathering evidence</span>
                {[0, 1, 2].map((i) => (
                  <motion.span
                    key={i}
                    initial={{ opacity: 0.2, y: 0 }}
                    animate={{ opacity: 1, y: -2 }}
                    transition={{
                      repeat: Infinity,
                      duration: 0.7,
                      delay: i * 0.15,
                      repeatType: "reverse",
                      ease: "easeInOut",
                    }}
                    className="h-1 w-1 rounded-full bg-accent"
                  />
                ))}
              </div>
            </motion.div>
          ) : error ? (
            <motion.div
              key="error"
              variants={bodyVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              transition={transition}
              className="flex items-start gap-3 rounded-xl border border-line-strong glass-strong p-4"
            >
              <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-accent-soft">
                <TriangleAlert className="h-4 w-4 text-accent" />
              </span>
              <div>
                <p className="text-sm font-medium text-ink">Something went wrong</p>
                <p className="mt-1 text-xs text-ink-soft">{error}</p>
              </div>
            </motion.div>
          ) : !response ? (
            <motion.div
              key="empty"
              variants={bodyVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              transition={transition}
              className="flex flex-col items-center px-4 py-16 text-center"
            >
              <motion.div
                animate={{ scale: [1, 1.06, 1] }}
                transition={{ repeat: Infinity, duration: 2.4, ease: "easeInOut" }}
                className="flex h-14 w-14 items-center justify-center rounded-2xl bg-accent-soft"
              >
                <MessageCircleQuestion className="h-7 w-7 text-accent" />
              </motion.div>
              <p className="mt-4 text-sm font-medium text-ink">
                Ask a question about your documents
              </p>
              <p className="mx-auto mt-1 max-w-sm text-xs text-ink-faint">
                Answers are grounded in your indexed sources with inline citations you can
                click to inspect.
              </p>
            </motion.div>
          ) : (
            <motion.div
              key="answer"
              variants={bodyVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              transition={transition}
            >
              {response.unanswerable_reason ? (
                <div className="flex items-start gap-3 rounded-xl border border-line-strong glass-strong p-4">
                  <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-accent-soft">
                    <TriangleAlert className="h-4 w-4 text-accent" />
                  </span>
                  <div>
                    <p className="text-sm font-medium text-ink">
                      Could not answer from current sources
                    </p>
                    <p className="mt-1 text-xs text-ink-soft">
                      {response.unanswerable_reason}
                    </p>
                  </div>
                </div>
              ) : (
                <>
                  <MarkdownRenderer
                    content={response.answer}
                    onCiteClick={setActiveCitationId}
                  />
                  <div className="my-4 border-t border-line" />
                  <CitationList
                    citations={response.citations}
                    activeCitationId={activeCitationId}
                    onSelect={setActiveCitationId}
                  />
                </>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </section>
  );
}
