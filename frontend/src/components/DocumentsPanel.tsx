"use client";

import { useRef } from "react";
import { FileText, Loader2, Plus, Table2, UploadCloud } from "lucide-react";
import { motion, AnimatePresence, type Variants } from "framer-motion";
import type { DocumentSummary } from "@/types";
import { cn } from "@/lib/utils";

interface DocumentsPanelProps {
  documents: DocumentSummary[];
  selectedDocId: string | null;
  onSelectDoc: (docId: string | null) => void;
  onUpload: (file: File) => Promise<void>;
  isLoading: boolean;
  isUploading: boolean;
  uploadError: string | null;
}

const listContainer: Variants = {
  hidden: {},
  show: {
    transition: { staggerChildren: 0.06, delayChildren: 0.08 },
  },
};

const listItem: Variants = {
  hidden: { opacity: 0, y: 10 },
  show: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.3, ease: "easeOut" },
  },
};

export function DocumentsPanel({
  documents,
  selectedDocId,
  onSelectDoc,
  onUpload,
  isLoading,
  isUploading,
  uploadError,
}: DocumentsPanelProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = async (
    e: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const file = e.target.files?.[0];
    if (!file) return;
    await onUpload(file);
    e.target.value = "";
  };

  return (
    <aside className="glass flex flex-col rounded-2xl">
      {/* Header + upload */}
      <div className="flex items-center justify-between border-b border-line px-4 py-3.5">
        <div>
          <h2 className="font-semibold text-ink">Documents</h2>
          <p className="mt-0.5 text-[11px] text-ink-faint">
            {documents.length} indexed
          </p>
        </div>
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={isUploading}
          className="inline-flex items-center gap-1.5 rounded-lg bg-accent px-3 py-1.5 text-xs font-medium text-white shadow-glow transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isUploading ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <Plus className="h-3.5 w-3.5" />
          )}
          Upload
        </button>
        <input
          ref={fileInputRef}
          type="file"
          accept="application/pdf"
          className="hidden"
          onChange={handleFileChange}
        />
      </div>

      {uploadError && (
        <div className="mx-4 mt-3 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-700 dark:text-red-300">
          {uploadError}
        </div>
      )}

      {/* Document list */}
      <div className="max-h-[460px] overflow-y-auto overscroll-contain p-2 [scrollbar-width:thin] [scrollbar-color:var(--line)_transparent] [&::-webkit-scrollbar]:w-1.5 [&::-webkit-scrollbar-track]:bg-transparent [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-thumb]:bg-line [&::-webkit-scrollbar-thumb]:hover:bg-line-strong">
        <AnimatePresence mode="wait">
          {isLoading ? (
            <motion.div
              key="loading"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.25 }}
              className="flex items-center justify-center gap-2 py-10 text-ink-faint"
            >
              <Loader2 className="h-4 w-4 animate-spin text-accent" />
              <span className="text-xs">Loading documents…</span>
            </motion.div>
          ) : documents.length === 0 ? (
            <motion.div
              key="empty"
              initial={{ opacity: 0, scale: 0.97 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.97 }}
              transition={{ duration: 0.25 }}
              className="px-4 py-10 text-center"
            >
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-accent-soft">
                <UploadCloud className="h-6 w-6 text-accent" />
              </div>
              <p className="mt-3 text-sm font-medium text-ink">
                No documents yet
              </p>
              <p className="mt-1 text-xs text-ink-faint">
                Upload a PDF to start asking questions.
              </p>
            </motion.div>
          ) : (
            <motion.ul
              key="list"
              variants={listContainer}
              initial="hidden"
              animate="show"
              exit={{ opacity: 0 }}
              className="space-y-1"
            >
              {/* All documents */}
              <motion.li variants={listItem} layout>
                <button
                  type="button"
                  onClick={() => onSelectDoc(null)}
                  className={cn(
                    "group flex w-full items-center gap-2.5 rounded-xl border px-3 py-2 text-left text-sm transition-transform duration-200 hover:-translate-y-px",
                    selectedDocId === null
                      ? "border-transparent bg-accent-soft text-accent"
                      : "border-transparent text-ink-soft hover:border-line-strong",
                  )}
                >
                  <FileText
                    className={cn(
                      "h-4 w-4 shrink-0 transition",
                      selectedDocId === null
                        ? "text-accent"
                        : "text-ink-faint group-hover:text-ink-soft",
                    )}
                  />
                  <span className="flex-1 truncate font-medium">
                    All documents
                  </span>
                  <span className="text-[11px] text-ink-faint">
                    {documents.reduce((n, d) => n + d.chunk_count, 0)} chunks
                  </span>
                </button>
              </motion.li>

              {documents.map((doc) => {
                const active = selectedDocId === doc.doc_id;
                return (
                  <motion.li key={doc.doc_id} variants={listItem} layout>
                    <button
                      type="button"
                      onClick={() => onSelectDoc(active ? null : doc.doc_id)}
                      className={cn(
                        "group flex w-full items-center gap-2.5 rounded-xl border px-3 py-2 text-left text-sm transition-transform duration-200 hover:-translate-y-px",
                        active
                          ? "border-transparent bg-accent-soft text-accent"
                          : "border-transparent text-ink-soft hover:border-line-strong",
                      )}
                    >
                      <FileText
                        className={cn(
                          "h-4 w-4 shrink-0 transition",
                          active
                            ? "text-accent"
                            : "text-ink-faint group-hover:text-ink-soft",
                        )}
                      />
                      <span className="min-w-0 flex-1">
                        <span
                          className={cn(
                            "block truncate font-medium",
                            active ? "text-accent" : "text-ink",
                          )}
                        >
                          {doc.filename}
                        </span>
                        <span className="block text-[11px] text-ink-faint">
                          {doc.chunk_count} chunks · {doc.page_count} pages
                          {doc.element_types.includes("table") && (
                            <span className="ml-1.5 inline-flex items-center gap-0.5">
                              <Table2 className="h-3 w-3" /> tables
                            </span>
                          )}
                        </span>
                      </span>
                    </button>
                  </motion.li>
                );
              })}
            </motion.ul>
          )}
        </AnimatePresence>
      </div>
    </aside>
  );
}
