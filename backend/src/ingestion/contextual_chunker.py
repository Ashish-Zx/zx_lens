"""Contextual chunking module for ClauseLens.

Splits parsed layout documents along natural section boundaries and table structures,
ensuring table integrity and prepending standardized contextual lineage headers.
"""

import logging
from typing import Any

from backend.src.schemas.document import (
    BoundingBox,
    DocumentChunk,
    ElementType,
    ParsedDocument,
    ParsedElement,
)

logger = logging.getLogger(__name__)


class ContextualChunker:
    """Production chunker that preserves table integrity and section breadcrumbs."""

    def __init__(
        self,
        max_chunk_chars: int = 1500,
        chunk_overlap_chars: int = 150,
    ) -> None:
        """Initialize chunker with character limits and overlap.

        Args:
            max_chunk_chars: Maximum character length for a single chunk (~350 tokens).
            chunk_overlap_chars: Character overlap between consecutive text chunks.
        """
        self.max_chunk_chars = max_chunk_chars
        self.chunk_overlap_chars = chunk_overlap_chars

    def chunk_document(self, parsed_doc: ParsedDocument) -> list[DocumentChunk]:
        """Convert a parsed document into contextualized chunks ready for indexing.

        Args:
            parsed_doc: Parsed document containing metadata and layout elements.

        Returns:
            List of DocumentChunk instances with deterministic IDs and headers.
        """
        chunks: list[DocumentChunk] = []
        doc_id = parsed_doc.metadata.doc_id
        filename = parsed_doc.metadata.filename
        chunk_sequence = 0

        # Buffer to accumulate text/list items within the same section & page
        current_buffer: list[ParsedElement] = []
        current_section = "Root"
        current_page = 1

        for element in parsed_doc.elements:
            # Tables are treated as first-class atomic or row-split units
            if element.element_type == ElementType.TABLE:
                if current_buffer:
                    chunk = self._flush_buffer(
                        buffer=current_buffer,
                        doc_id=doc_id,
                        filename=filename,
                        chunk_index=chunk_sequence,
                        section_path=current_section,
                        page_number=current_page,
                    )
                    chunks.append(chunk)
                    chunk_sequence += 1
                    current_buffer = []

                table_chunks = self._chunk_table(
                    element=element,
                    doc_id=doc_id,
                    filename=filename,
                    start_index=chunk_sequence,
                )
                chunks.extend(table_chunks)
                chunk_sequence += len(table_chunks)
                continue

            # If section or page changes, flush existing buffer
            if (
                current_buffer
                and (
                    element.section_path != current_section
                    or element.page_number != current_page
                )
            ):
                chunk = self._flush_buffer(
                    buffer=current_buffer,
                    doc_id=doc_id,
                    filename=filename,
                    chunk_index=chunk_sequence,
                    section_path=current_section,
                    page_number=current_page,
                )
                chunks.append(chunk)
                chunk_sequence += 1
                current_buffer = []

            # Check if adding this element exceeds max_chunk_chars
            tentative_len = sum(len(e.content) + 2 for e in current_buffer) + len(element.content)
            if tentative_len > self.max_chunk_chars and current_buffer:
                chunk = self._flush_buffer(
                    buffer=current_buffer,
                    doc_id=doc_id,
                    filename=filename,
                    chunk_index=chunk_sequence,
                    section_path=current_section,
                    page_number=current_page,
                )
                chunks.append(chunk)
                chunk_sequence += 1
                current_buffer = []

            current_buffer.append(element)
            current_section = element.section_path
            current_page = element.page_number

        # Flush any remaining elements in buffer
        if current_buffer:
            chunk = self._flush_buffer(
                buffer=current_buffer,
                doc_id=doc_id,
                filename=filename,
                chunk_index=chunk_sequence,
                section_path=current_section,
                page_number=current_page,
            )
            chunks.append(chunk)

        logger.info(
            "Chunked document %s (%s) into %d contextual chunks",
            filename,
            doc_id,
            len(chunks),
        )
        return chunks

    def _flush_buffer(
        self,
        buffer: list[ParsedElement],
        doc_id: str,
        filename: str,
        chunk_index: int,
        section_path: str,
        page_number: int,
    ) -> DocumentChunk:
        """Combine buffered layout elements into a single contextualized DocumentChunk."""
        raw_text = "\n\n".join(e.content for e in buffer).strip()
        contextualized_text = DocumentChunk.build_contextual_header(
            filename=filename,
            page_number=page_number,
            section_path=section_path,
            content=raw_text,
        )

        bbox = self._merge_bounding_boxes(
            [e.bounding_box for e in buffer if e.bounding_box is not None]
        )
        chunk_id = DocumentChunk.generate_chunk_id(
            doc_id=doc_id,
            page_number=page_number,
            chunk_index=chunk_index,
        )

        return DocumentChunk(
            chunk_id=chunk_id,
            doc_id=doc_id,
            filename=filename,
            page_number=page_number,
            chunk_index=chunk_index,
            element_type=ElementType.TEXT,
            section_path=section_path,
            raw_content=raw_text,
            contextualized_content=contextualized_text,
            bounding_box=bbox,
        )

    def _chunk_table(
        self,
        element: ParsedElement,
        doc_id: str,
        filename: str,
        start_index: int,
    ) -> list[DocumentChunk]:
        """Split a Markdown table by rows if it exceeds max_chunk_chars, repeating headers."""
        raw_table = element.content.strip()

        # If table fits comfortably within character budget, keep it intact
        if len(raw_table) <= self.max_chunk_chars:
            chunk_id = DocumentChunk.generate_chunk_id(
                doc_id=doc_id,
                page_number=element.page_number,
                chunk_index=start_index,
            )
            contextualized = DocumentChunk.build_contextual_header(
                filename=filename,
                page_number=element.page_number,
                section_path=element.section_path,
                content=raw_table,
            )
            return [
                DocumentChunk(
                    chunk_id=chunk_id,
                    doc_id=doc_id,
                    filename=filename,
                    page_number=element.page_number,
                    chunk_index=start_index,
                    element_type=ElementType.TABLE,
                    section_path=element.section_path,
                    raw_content=raw_table,
                    contextualized_content=contextualized,
                    bounding_box=element.bounding_box,
                )
            ]

        # Table exceeds limit: split by row while preserving Markdown header row & separator
        lines = [line.strip() for line in raw_table.splitlines() if line.strip()]
        if len(lines) <= 2:
            # Fallback if structure is minimal
            chunk_id = DocumentChunk.generate_chunk_id(
                doc_id=doc_id,
                page_number=element.page_number,
                chunk_index=start_index,
            )
            return [
                DocumentChunk(
                    chunk_id=chunk_id,
                    doc_id=doc_id,
                    filename=filename,
                    page_number=element.page_number,
                    chunk_index=start_index,
                    element_type=ElementType.TABLE,
                    section_path=element.section_path,
                    raw_content=raw_table,
                    contextualized_content=DocumentChunk.build_contextual_header(
                        filename, element.page_number, element.section_path, raw_table
                    ),
                    bounding_box=element.bounding_box,
                )
            ]

        header_lines = lines[:2]  # Header text and markdown divider line
        header_block = "\n".join(header_lines)
        row_lines = lines[2:]

        sub_chunks: list[DocumentChunk] = []
        current_rows: list[str] = []
        current_char_count = len(header_block)
        current_seq = start_index

        for row in row_lines:
            row_len = len(row) + 1
            if current_rows and (current_char_count + row_len > self.max_chunk_chars):
                sub_table = f"{header_block}\n" + "\n".join(current_rows)
                chunk_id = DocumentChunk.generate_chunk_id(
                    doc_id=doc_id,
                    page_number=element.page_number,
                    chunk_index=current_seq,
                )
                sub_chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        doc_id=doc_id,
                        filename=filename,
                        page_number=element.page_number,
                        chunk_index=current_seq,
                        element_type=ElementType.TABLE,
                        section_path=element.section_path,
                        raw_content=sub_table,
                        contextualized_content=DocumentChunk.build_contextual_header(
                            filename, element.page_number, element.section_path, sub_table
                        ),
                        bounding_box=element.bounding_box,
                    )
                )
                current_seq += 1
                current_rows = []
                current_char_count = len(header_block)

            current_rows.append(row)
            current_char_count += row_len

        if current_rows:
            sub_table = f"{header_block}\n" + "\n".join(current_rows)
            chunk_id = DocumentChunk.generate_chunk_id(
                doc_id=doc_id,
                page_number=element.page_number,
                chunk_index=current_seq,
            )
            sub_chunks.append(
                DocumentChunk(
                    chunk_id=chunk_id,
                    doc_id=doc_id,
                    filename=filename,
                    page_number=element.page_number,
                    chunk_index=current_seq,
                    element_type=ElementType.TABLE,
                    section_path=element.section_path,
                    raw_content=sub_table,
                    contextualized_content=DocumentChunk.build_contextual_header(
                        filename, element.page_number, element.section_path, sub_table
                    ),
                    bounding_box=element.bounding_box,
                )
            )

        return sub_chunks

    def _merge_bounding_boxes(
        self,
        boxes: list[BoundingBox],
    ) -> BoundingBox | None:
        """Compute the minimum bounding rectangle enclosing all constituent boxes."""
        if not boxes:
            return None
        if len(boxes) == 1:
            return boxes[0]

        min_l = min(b.l for b in boxes)
        min_t = min(b.t for b in boxes)
        max_r = max(b.r for b in boxes)
        max_b = max(b.b for b in boxes)
        page_no = boxes[0].page_number
        origin = boxes[0].coord_origin

        return BoundingBox(
            l=min_l,
            t=min_t,
            r=max_r,
            b=max_b,
            page_number=page_no,
            coord_origin=origin,
        )

