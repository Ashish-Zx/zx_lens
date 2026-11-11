"use client";

import { useCallback, useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowDown, FolderOpen, X } from "lucide-react";
import { DocumentSummary, IndexStats, RAGResponse } from "@/types";
import { api } from "@/lib/api";
import { Header } from "@/components/Header";
import { AnimatedBackground } from "@/components/AnimatedBackground";
import { PipelineFlow } from "@/components/PipelineFlow";
import { DocumentsPanel } from "@/components/DocumentsPanel";
import { AskInput } from "@/components/AskInput";
import { AnswerPanel } from "@/components/AnswerPanel";

export default function Home() {
  const [stats, setStats] = useState<IndexStats | null>(null);
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [docsLoading, setDocsLoading] = useState(true);

  const [queryInput, setQueryInput] = useState("");
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);

  const [response, setResponse] = useState<RAGResponse | null>(null);
  const [isAsking, setIsAsking] = useState(false);
  const [askError, setAskError] = useState<string | null>(null);

  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const [drawerOpen, setDrawerOpen] = useState(false);

  const refreshData = useCallback(async () => {
    try {
      const [statsData, docs] = await Promise.all([
        api.getStats(),
        api.listDocuments(),
      ]);
      setStats(statsData);
      setDocuments(docs);
    } catch {
      // backend may be offline; keep empty state
    } finally {
      setDocsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshData();
  }, [refreshData]);

  const handleAsk = useCallback(async () => {
    const query = queryInput.trim();
    if (query.length < 2 || isAsking) return;

    setIsAsking(true);
    setAskError(null);
    try {
      const result = await api.ask({
        query,
        doc_ids: selectedDocId ? [selectedDocId] : null,
      });
      setResponse(result);
    } catch (err) {
      setAskError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setIsAsking(false);
    }
  }, [queryInput, isAsking, selectedDocId]);

  const handleUpload = useCallback(
    async (file: File) => {
      setIsUploading(true);
      setUploadError(null);
      try {
        await api.uploadDocument(file);
        await refreshData();
      } catch (err) {
        setUploadError(err instanceof Error ? err.message : "Upload failed");
      } finally {
        setIsUploading(false);
      }
    },
    [refreshData]
  );

  const handleSelectDoc = useCallback((docId: string | null) => {
    setSelectedDocId(docId);
    setDrawerOpen(false);
  }, []);

  const selectedDoc = documents.find((d) => d.doc_id === selectedDocId) ?? null;

  const scrollTo = useCallback((id: string) => {
    document.getElementById(id)?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  }, []);

  return (
    <>
      <AnimatedBackground />
      <Header stats={stats} />

      <main className="relative mx-auto w-full max-w-6xl flex-1 px-4 py-10 sm:px-6 lg:px-8">
        {/* Hero */}
        <motion.section
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
          className="mx-auto max-w-3xl text-center"
        >
          <span className="glass inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium text-ink-soft">
            <span className="h-1.5 w-1.5 rounded-full bg-accent" />
            Grounded AI search for your documents
          </span>
          <h1 className="mt-5 text-4xl font-bold tracking-tight text-ink sm:text-5xl">
            Ask anything about your{" "}
            <span className="bg-gradient-to-r from-accent to-accent-strong bg-clip-text text-transparent">
              documents
            </span>
          </h1>
          <p className="mx-auto mt-4 max-w-lg text-base text-ink-faint">
            Upload a PDF, type a question, and get a clear answer generated
            only from your files — with citations you can verify.
          </p>

          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <button
              type="button"
              onClick={() => scrollTo("try")}
              className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-accent to-accent-strong px-6 py-3 text-sm font-semibold text-white shadow-glow transition hover:brightness-110"
            >
              Try it now
              <ArrowDown className="h-4 w-4" />
            </button>
            <button
              type="button"
              onClick={() => scrollTo("how")}
              className="glass inline-flex items-center gap-2 rounded-xl px-6 py-3 text-sm font-semibold text-ink-soft transition hover:text-ink"
            >
              See how it works
            </button>
          </div>
        </motion.section>

        {/* Behind-the-scenes pipeline */}
        <div id="how" className="scroll-mt-24">
          <PipelineFlow />
        </div>

        {/* Try it — live workspace */}
        <div id="try" className="mt-24 scroll-mt-24">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-80px" }}
            transition={{ duration: 0.5 }}
            className="mx-auto mb-8 max-w-xl text-center"
          >
            <h2 className="text-2xl font-bold tracking-tight text-ink sm:text-3xl">
              Ready to try it?
            </h2>
            <p className="mx-auto mt-3 max-w-md text-sm text-ink-faint">
              Drop in a PDF, then ask your first question below.
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-60px" }}
            transition={{ duration: 0.55, ease: "easeOut" }}
          >
            <div className="mb-6">
              <AskInput
                value={queryInput}
                onChange={setQueryInput}
                onAsk={handleAsk}
                isLoading={isAsking}
              />
              {selectedDoc && (
                <div className="mt-2.5 inline-flex items-center gap-2 rounded-full border border-line bg-surface/60 px-3 py-1 text-xs text-ink-soft">
                  Searching within{" "}
                  <span className="font-medium text-ink">
                    {selectedDoc.filename}
                  </span>
                  <button
                    type="button"
                    onClick={() => setSelectedDocId(null)}
                    className="text-ink-faint transition hover:text-ink"
                    aria-label="Clear document filter"
                  >
                    <X className="h-3.5 w-3.5" />
                  </button>
                </div>
              )}
            </div>

            <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
              <div className="hidden lg:col-span-4 lg:block">
                <DocumentsPanel
                  documents={documents}
                  selectedDocId={selectedDocId}
                  onSelectDoc={handleSelectDoc}
                  onUpload={handleUpload}
                  isLoading={docsLoading}
                  isUploading={isUploading}
                  uploadError={uploadError}
                />
              </div>

              <div className="lg:col-span-8">
                <div className="mb-4 flex items-center justify-between lg:hidden">
                  <span className="text-xs font-medium uppercase tracking-wider text-ink-faint">
                    Workspace
                  </span>
                  <button
                    type="button"
                    onClick={() => setDrawerOpen(true)}
                    className="glass inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium text-ink-soft transition hover:text-ink"
                  >
                    <FolderOpen className="h-3.5 w-3.5 text-accent" />
                    Documents ({documents.length})
                  </button>
                </div>
                <AnswerPanel
                  response={response}
                  isLoading={isAsking}
                  error={askError}
                />
              </div>
            </div>
          </motion.div>
        </div>
      </main>

      <footer className="py-5 text-center text-xs text-ink-faint">
        Zx Lens — grounded answers from your documents
      </footer>

      {/* Mobile documents drawer */}
      <AnimatePresence>
        {drawerOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 lg:hidden"
          >
            <div
              className="absolute inset-0 bg-black/30 backdrop-blur-sm"
              onClick={() => setDrawerOpen(false)}
            />
            <motion.div
              initial={{ x: -320 }}
              animate={{ x: 0 }}
              exit={{ x: -320 }}
              transition={{ type: "spring", damping: 30, stiffness: 300 }}
              className="absolute inset-y-0 left-0 w-[86%] max-w-sm p-4"
            >
              <DocumentsPanel
                documents={documents}
                selectedDocId={selectedDocId}
                onSelectDoc={handleSelectDoc}
                onUpload={handleUpload}
                isLoading={docsLoading}
                isUploading={isUploading}
                uploadError={uploadError}
              />
              <button
                type="button"
                onClick={() => setDrawerOpen(false)}
                className="glass mt-3 inline-flex w-full items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium text-ink-soft transition hover:text-ink"
              >
                <X className="h-4 w-4" /> Close
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
