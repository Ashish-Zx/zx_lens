/** TypeScript data contracts for Zx Lens, matching the backend Pydantic schemas. */

export type ElementType = "text" | "table" | "section_header" | "list_item";

export interface BoundingBox {
  l: number;
  t: number;
  r: number;
  b: number;
  page_number: number;
  coord_origin: string;
}

/** Aggregated summary of one indexed document (GET /documents/list). */
export interface DocumentSummary {
  doc_id: string;
  filename: string;
  chunk_count: number;
  page_count: number;
  pages: number[];
  element_types: ElementType[];
}

/** Index storage counts (GET /documents/stats). */
export interface IndexStats {
  dense_count: number;
  sparse_count: number;
}

/** Result of uploading + indexing a document. */
export interface IngestionResponse {
  doc_id: string;
  filename: string;
  page_count: number;
  chunk_count: number;
  table_count: number;
  status: string;
}

export interface QueryRequest {
  query: string;
  doc_ids?: string[] | null;
  top_k?: number | null;
}

/** A grounded citation backing a claim in the generated answer. */
export interface Citation {
  citation_id: number;
  chunk_id: string;
  doc_name: string;
  page_number: number;
  section_path: string;
  verbatim_quote: string;
  bounding_box: BoundingBox | null;
}

/** Final grounded synthesis returned by /query/ask. */
export interface RAGResponse {
  query: string;
  answer: string;
  citations: Citation[];
  unanswerable_reason: string | null;
  total_latency_ms: number;
}
