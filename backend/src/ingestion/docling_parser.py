"""Docling document parser for ClauseLens.

Extracts layout-aware structural hierarchies, OCR text, and exact tables
from PDFs using Docling's DocumentConverter with TableFormer ACCURATE mode.
"""

from datetime import datetime, timezone
import hashlib
import logging
from pathlib import Path
from typing import Any

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TableFormerMode
from docling.document_converter import DocumentConverter, PdfFormatOption

from backend.src.exceptions import DocumentParsingError
from backend.src.schemas.document import (
    BoundingBox,
    DocumentMetadata,
    ElementType,
    ParsedDocument,
    ParsedElement,
)

logger = logging.getLogger(__name__)


class DoclingParser:
    """Production-grade layout parser wrapping Docling."""

    def __init__(self, do_ocr: bool = True, accurate_tables: bool = True) -> None:
        """Initialize the Docling parser with OCR and TableFormer options."""
        self._pipeline_options = PdfPipelineOptions(
            do_ocr=do_ocr,
            do_table_structure=True,
        )
        if accurate_tables:
            self._pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE

        self._converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=self._pipeline_options)
            }
        )
        logger.info(
            "DoclingParser initialized (ocr=%s, accurate_tables=%s)",
            do_ocr,
            accurate_tables,
        )

    def parse_pdf(
        self,
        file_path: str | Path,
        doc_id: str | None = None,
    ) -> ParsedDocument:
        """Parse a PDF document into layout elements and metadata.

        Args:
            file_path: Path to the target PDF file.
            doc_id: Optional unique identifier. Defaults to SHA-256 hash of file.

        Returns:
            ParsedDocument containing metadata and ordered layout elements.

        Raises:
            DocumentParsingError: If file is missing or Docling parsing fails.
        """
        path = Path(file_path).resolve()
        if not path.exists():
            raise DocumentParsingError(
                f"Document file not found: {path}",
                details={"file_path": str(path)},
            )
        if not path.is_file():
            raise DocumentParsingError(
                f"Target path is not a file: {path}",
                details={"file_path": str(path)},
            )

        try:
            file_bytes = path.read_bytes()
            computed_doc_id = doc_id or hashlib.sha256(file_bytes).hexdigest()[:16]
            file_size_bytes = len(file_bytes)

            logger.info("Starting Docling conversion for %s (doc_id=%s)", path.name, computed_doc_id)
            conv_res = self._converter.convert(path)
            doc = conv_res.document

            page_count = len(doc.pages) if hasattr(doc, "pages") and doc.pages else 1
            metadata = DocumentMetadata(
                doc_id=computed_doc_id,
                filename=path.name,
                page_count=page_count,
                file_size_bytes=file_size_bytes,
                created_at=datetime.now(timezone.utc),
            )

            elements: list[ParsedElement] = []
            header_stack: list[tuple[int, str]] = []

            # Traverse all layout items in document reading order
            for item, level in doc.iterate_items():
                element_type, content = self._extract_content(item)
                if not content:
                    continue

                # Maintain hierarchical section breadcrumb stack
                if element_type == ElementType.SECTION_HEADER:
                    self._update_header_stack(header_stack, level=level, title=content)

                current_section_path = self._format_breadcrumb(header_stack)
                bounding_box = self._extract_bounding_box(item)
                page_number = bounding_box.page_number if bounding_box else 1

                elements.append(
                    ParsedElement(
                        element_type=element_type,
                        content=content,
                        page_number=page_number,
                        section_path=current_section_path,
                        bounding_box=bounding_box,
                    )
                )

            logger.info(
                "Successfully parsed %s: %d layout elements across %d pages",
                path.name,
                len(elements),
                page_count,
            )
            return ParsedDocument(metadata=metadata, elements=elements)

        except DocumentParsingError:
            raise
        except Exception as exc:
            logger.exception("Failed to parse document %s: %s", path.name, str(exc))
            raise DocumentParsingError(
                f"Docling conversion failed for {path.name}: {exc}",
                details={"file_path": str(path), "error": str(exc)},
            ) from exc

    def _extract_content(self, item: Any) -> tuple[ElementType, str]:
        """Classify item type and extract its clean text representation."""
        label = getattr(item, "label", None)
        label_str = str(label).lower() if label else ""

        # Handle tables via Docling's markdown export
        if hasattr(item, "export_to_markdown") and "table" in label_str:
            md_table = item.export_to_markdown()
            return ElementType.TABLE, md_table.strip()

        # Handle text items
        text = getattr(item, "text", "")
        if not text:
            return ElementType.TEXT, ""

        clean_text = text.strip()
        if "section_header" in label_str or "title" in label_str or "heading" in label_str:
            return ElementType.SECTION_HEADER, clean_text
        if "list" in label_str:
            return ElementType.LIST_ITEM, clean_text

        return ElementType.TEXT, clean_text

    def _extract_bounding_box(self, item: Any) -> BoundingBox | None:
        """Extract first available provenance bounding box from layout item."""
        prov_list = getattr(item, "prov", None)
        if not prov_list or not isinstance(prov_list, list):
            return None

        first_prov = prov_list[0]
        page_no = getattr(first_prov, "page_no", 1)
        bbox = getattr(first_prov, "bbox", None)
        if not bbox:
            return None

        coord_origin = str(getattr(bbox, "coord_origin", "TOPLEFT"))
        return BoundingBox(
            l=float(bbox.l),
            t=float(bbox.t),
            r=float(bbox.r),
            b=float(bbox.b),
            page_number=max(1, int(page_no)),
            coord_origin=coord_origin,
        )

    def _update_header_stack(
        self,
        stack: list[tuple[int, str]],
        level: int,
        title: str,
    ) -> None:
        """Maintain header depth hierarchy when entering a new section."""
        while stack and stack[-1][0] >= level:
            stack.pop()
        stack.append((level, title.strip()))

    def _format_breadcrumb(self, stack: list[tuple[int, str]]) -> str:
        """Format the current header hierarchy into a readable breadcrumb string."""
        if not stack:
            return "Root"
        return " > ".join(title for _, title in stack)

