"use client";

import { motion } from "framer-motion";
import { Loader2, SendHorizonal } from "lucide-react";

interface AskInputProps {
  value: string;
  onChange: (value: string) => void;
  onAsk: () => void;
  isLoading: boolean;
  placeholder?: string;
}

export function AskInput({
  value,
  onChange,
  onAsk,
  isLoading,
  placeholder = "Ask a question about your documents…",
}: AskInputProps) {
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !isLoading && value.trim().length >= 2) {
      onAsk();
    }
  };

  return (
    <div className="glass-strong group flex items-center gap-2 rounded-2xl px-4 py-3 transition-shadow focus-within:shadow-glow">
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        className="flex-1 bg-transparent text-[15px] text-ink placeholder:text-ink-faint focus:outline-none"
      />
      <motion.button
        type="button"
        onClick={onAsk}
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.9 }}
        disabled={isLoading || value.trim().length < 2}
        className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-r from-accent to-accent-strong text-white shadow-glow transition disabled:opacity-40"
        aria-label="Ask"
      >
        {isLoading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <SendHorizonal className="h-4 w-4" />
        )}
      </motion.button>
    </div>
  );
}
