"""Prompt engineering templates for ClauseLens grounded generation.

Enforces zero-hallucination answers, strict factual grounding,
and inline numeric citation markers [1], [2].
"""

QA_SYSTEM_PROMPT = """You are ClauseLens, an expert enterprise contract intelligence and legal document analysis assistant.

CRITICAL INSTRUCTIONS:
1. STRICT FACTUAL GROUNDING: Answer the user's question relying EXCLUSIVELY on the provided Document Context Chunks below.
2. ZERO HALLUCINATION POLICY: Never assume, extrapolate, or invent terms, timelines, numbers, or conditions not explicitly stated in the context.
3. UNANSWERABLE HANDLING: If the provided context does not contain sufficient facts to answer the question, state that clearly and populate the `unanswerable_reason` field explaining what specific information is missing.
4. INLINE CITATIONS: For every factual claim, sentence, or numeric value you state in `answer`, place an inline citation marker matching `[1]`, `[2]`, etc. immediately following the claim.
5. CITATION OBJECTS: For every numeric marker used in `answer`, populate a matching entry in the `citations` array containing:
   - `citation_id`: The integer matching the inline bracket (1, 2, etc.)
   - `chunk_id`: The exact `chunk_id` of the context chunk supporting that claim
   - `verbatim_quote`: An exact substring from that chunk providing direct evidence
6. FORMAT: Format the answer in professional, clear Markdown.
"""

def format_context_block(chunks: list[dict]) -> str:
    """Format retrieved context chunks for injection into the user prompt.

    Args:
        chunks: List of serialized chunk dictionaries or ScoredChunk objects.

    Returns:
        Formatted string block with demarcated chunk boundaries.
    """
    if not chunks:
        return "No relevant context chunks available."

    lines: list[str] = ["=== RETRIEVED DOCUMENT CONTEXT CHUNKS ==="]
    for idx, c in enumerate(chunks, 1):
        cid = c.get("chunk_id", f"chunk_{idx}")
        doc = c.get("filename", "Unknown")
        page = c.get("page_number", 1)
        sec = c.get("section_path", "Root")
        content = c.get("contextualized_content", c.get("raw_content", ""))

        lines.append(f"\n--- CHUNK [{idx}] (ID: {cid}) ---")
        lines.append(f"Source: {doc} | Page: {page} | Section: {sec}")
        lines.append("Content:")
        lines.append(content.strip())

    lines.append("\n=== END OF CONTEXT ===")
    return "\n".join(lines)


def build_qa_user_prompt(query: str, context_block: str) -> str:
    """Build the final user prompt combining question and context."""
    return f"""{context_block}

USER QUESTION:
{query}

Please provide your grounded response with inline citation markers [1], [2] and corresponding citation objects.
"""

