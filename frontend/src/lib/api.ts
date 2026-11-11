import {
  DocumentSummary,
  IndexStats,
  IngestionResponse,
  QueryRequest,
  RAGResponse,
} from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

class APIError extends Error {
  constructor(
    public status: number,
    message: string,
    public details?: Record<string, unknown>
  ) {
    super(message);
    this.name = "APIError";
  }
}

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const body = (await response.json()) as { detail?: string; message?: string };
      message = body.detail || body.message || message;
    } catch {
      // non-JSON error
    }
    throw new APIError(response.status, message);
  }

  return (await response.json()) as T;
}

export const api = {
  /** Fetch storage stats for dense and sparse indexes. */
  async getStats(): Promise<IndexStats> {
    return request<IndexStats>("/documents/stats");
  },

  /** List all indexed documents with aggregate summaries. */
  async listDocuments(): Promise<DocumentSummary[]> {
    return request<DocumentSummary[]>("/documents/list");
  },

  /** Upload and index a PDF document. */
  async uploadDocument(file: File): Promise<IngestionResponse> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${API_BASE_URL}/documents/upload`, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      let message = "Upload failed";
      try {
        const body = (await response.json()) as { detail?: string };
        message = body.detail || message;
      } catch {
        // ignore
      }
      throw new APIError(response.status, message);
    }

    return (await response.json()) as IngestionResponse;
  },

  /** Ask a question and receive a grounded answer with citations. */
  async ask(requestPayload: QueryRequest): Promise<RAGResponse> {
    return request<RAGResponse>("/query/ask", {
      method: "POST",
      body: JSON.stringify(requestPayload),
    });
  },
};
