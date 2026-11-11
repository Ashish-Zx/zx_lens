import { motion } from "framer-motion";
import { FileText } from "lucide-react";
import { Citation } from "@/types";

interface CitationListProps {
  citations: Citation[];
  activeCitationId: number | null;
  onSelect: (citationId: number) => void;
}

export function CitationList({
  citations,
  activeCitationId,
  onSelect,
}: CitationListProps) {
  if (citations.length === 0) return null;

  return (
    <div className="mt-6">
      <h3 className="text-xs font-semibold uppercase tracking-wider text-ink-faint">
        Sources ({citations.length})
      </h3>
      <ul className="mt-2 space-y-2">
        {citations.map((citation) => {
          const active = activeCitationId === citation.citation_id;
          return (
            <motion.li
              key={citation.citation_id}
              layout
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, ease: "easeOut" }}
            >
              <motion.button
                type="button"
                onClick={() => onSelect(citation.citation_id)}
                whileHover={{ scale: 1.012 }}
                whileTap={{ scale: 0.99 }}
                className={`w-full rounded-xl border p-3 text-left transition-colors ${
                  active
                    ? "border-line-strong bg-accent-soft shadow-glow"
                    : "border-line glass hover:border-line-strong"
                }`}
              >
                <div className="flex items-center gap-2">
                  <span className="inline-flex h-5 items-center rounded-md bg-accent px-1.5 font-mono text-[10px] font-bold text-white">
                    [{citation.citation_id}]
                  </span>
                  <span className="flex items-center gap-1.5 truncate text-sm font-medium text-ink">
                    <FileText className="h-3.5 w-3.5 text-accent" />
                    {citation.doc_name}
                  </span>
                  <span className="ml-auto shrink-0 font-mono text-[11px] text-ink-faint">
                    p.{citation.page_number}
                  </span>
                </div>
                {citation.section_path && (
                  <p className="mt-1 text-[11px] text-ink-faint">
                    {citation.section_path}
                  </p>
                )}
                <p className="mt-1.5 text-[13px] leading-relaxed text-ink-soft">
                  “{citation.verbatim_quote}”
                </p>
              </motion.button>
            </motion.li>
          );
        })}
      </ul>
    </div>
  );
}
