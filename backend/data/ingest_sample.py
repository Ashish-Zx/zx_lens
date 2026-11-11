"""Ingest sample contract clauses into the persistent dual store."""

from datetime import datetime, timezone
from pathlib import Path

from backend.src.indexing.index_manager import IndexManager
from backend.src.schemas.document import (
    BoundingBox,
    DocumentChunk,
    ElementType,
)


def populate_sample_contract_index() -> None:
    """Populate persistent Chroma and BM25 stores with golden contract clauses."""
    index_manager = IndexManager()

    doc_id = "msa_2024_delaware"
    filename = "Master_Services_Agreement_2024.pdf"

    chunks = [
        DocumentChunk(
            chunk_id=DocumentChunk.generate_chunk_id(doc_id, 1, 0),
            doc_id=doc_id,
            filename=filename,
            page_number=1,
            chunk_index=0,
            element_type=ElementType.TEXT,
            section_path="Article 1: Definitions",
            raw_content=(
                "\"Authorized User\" means employees and contractors authorized by Customer to access the Services. "
                "\"Confidential Information\" includes all technical, business, and pricing data disclosed by one party to the other."
            ),
            contextualized_content=DocumentChunk.build_contextual_header(
                filename, 1, "Article 1: Definitions",
                "\"Authorized User\" means employees and contractors authorized by Customer to access the Services. "
                "\"Confidential Information\" includes all technical, business, and pricing data disclosed by one party to the other."
            ),
            bounding_box=BoundingBox(l=50.0, t=100.0, r=500.0, b=180.0, page_number=1),
        ),
        DocumentChunk(
            chunk_id=DocumentChunk.generate_chunk_id(doc_id, 4, 1),
            doc_id=doc_id,
            filename=filename,
            page_number=4,
            chunk_index=1,
            element_type=ElementType.TEXT,
            section_path="Article 11: Limitation of Liability > 11.4 Caps",
            raw_content=(
                "Section 11.4(b) Limitation of Liability: IN NO EVENT SHALL EITHER PARTY BE LIABLE FOR ANY INDIRECT, "
                "INCIDENTAL, SPECIAL, OR CONSEQUENTIAL DAMAGES. EACH PARTY'S TOTAL AGGREGATE LIABILITY ARISING OUT OF THIS "
                "AGREEMENT SHALL BE CAPPED AT TWELVE (12) MONTHS OF FEES PAID PRECEDING THE CLAIM OR $1,500,000, WHICHEVER IS GREATER."
            ),
            contextualized_content=DocumentChunk.build_contextual_header(
                filename, 4, "Article 11: Limitation of Liability > 11.4 Caps",
                "Section 11.4(b) Limitation of Liability: IN NO EVENT SHALL EITHER PARTY BE LIABLE FOR ANY INDIRECT, "
                "INCIDENTAL, SPECIAL, OR CONSEQUENTIAL DAMAGES. EACH PARTY'S TOTAL AGGREGATE LIABILITY ARISING OUT OF THIS "
                "AGREEMENT SHALL BE CAPPED AT TWELVE (12) MONTHS OF FEES PAID PRECEDING THE CLAIM OR $1,500,000, WHICHEVER IS GREATER."
            ),
            bounding_box=BoundingBox(l=50.0, t=320.0, r=520.0, b=410.0, page_number=4),
        ),
        DocumentChunk(
            chunk_id=DocumentChunk.generate_chunk_id(doc_id, 6, 2),
            doc_id=doc_id,
            filename="Security_Addendum.pdf",
            page_number=6,
            chunk_index=2,
            element_type=ElementType.TEXT,
            section_path="Schedule C: Security Addendum > Section 3 Audits",
            raw_content=(
                "Vendor warrants that it shall maintain annual SOC-2 Type II certification and ISO 27001 compliance throughout "
                "the term of this Agreement. Upon written request, Vendor shall provide Customer with a copy of its current SOC-2 Type II audit report within thirty (30) days of completion."
            ),
            contextualized_content=DocumentChunk.build_contextual_header(
                "Security_Addendum.pdf", 6, "Schedule C: Security Addendum > Section 3 Audits",
                "Vendor warrants that it shall maintain annual SOC-2 Type II certification and ISO 27001 compliance throughout "
                "the term of this Agreement. Upon written request, Vendor shall provide Customer with a copy of its current SOC-2 Type II audit report within thirty (30) days of completion."
            ),
            bounding_box=BoundingBox(l=50.0, t=150.0, r=510.0, b=240.0, page_number=6),
        ),
        DocumentChunk(
            chunk_id=DocumentChunk.generate_chunk_id(doc_id, 8, 3),
            doc_id=doc_id,
            filename="SLA_Agreement.pdf",
            page_number=8,
            chunk_index=3,
            element_type=ElementType.TABLE,
            section_path="Schedule B: Service Level Agreement > Section 2 SLA Credits",
            raw_content=(
                "| Service Tier | Monthly Fee | Uptime Guarantee | SLA Credit for Downtime |\n"
                "| :--- | :--- | :--- | :--- |\n"
                "| Standard | $5,000 | 99.5% | 5% credit if uptime < 99.5% |\n"
                "| Enterprise | $15,000 | 99.9% | 10% credit (99.0% - 99.89%), 25% credit (< 99.0%) |\n"
                "| Mission Critical | $35,000 | 99.99% | 20% credit (99.5% - 99.98%), 50% credit (< 99.5%) |"
            ),
            contextualized_content=DocumentChunk.build_contextual_header(
                "SLA_Agreement.pdf", 8, "Schedule B: Service Level Agreement > Section 2 SLA Credits",
                "| Service Tier | Monthly Fee | Uptime Guarantee | SLA Credit for Downtime |\n"
                "| :--- | :--- | :--- | :--- |\n"
                "| Standard | $5,000 | 99.5% | 5% credit if uptime < 99.5% |\n"
                "| Enterprise | $15,000 | 99.9% | 10% credit (99.0% - 99.89%), 25% credit (< 99.0%) |\n"
                "| Mission Critical | $35,000 | 99.99% | 20% credit (99.5% - 99.98%), 50% credit (< 99.5%) |"
            ),
            bounding_box=BoundingBox(l=40.0, t=200.0, r=550.0, b=350.0, page_number=8),
        ),
        DocumentChunk(
            chunk_id=DocumentChunk.generate_chunk_id(doc_id, 9, 4),
            doc_id=doc_id,
            filename=filename,
            page_number=9,
            chunk_index=4,
            element_type=ElementType.TEXT,
            section_path="Article 14: Term and Termination > 14.2 Termination for Convenience",
            raw_content=(
                "Section 14.2 Termination for Convenience: Either party may terminate this Agreement without cause "
                "upon providing at least sixty (60) days prior written notice to the other party."
            ),
            contextualized_content=DocumentChunk.build_contextual_header(
                filename, 9, "Article 14: Term and Termination > 14.2 Termination for Convenience",
                "Section 14.2 Termination for Convenience: Either party may terminate this Agreement without cause "
                "upon providing at least sixty (60) days prior written notice to the other party."
            ),
            bounding_box=BoundingBox(l=50.0, t=110.0, r=510.0, b=180.0, page_number=9),
        ),
        DocumentChunk(
            chunk_id=DocumentChunk.generate_chunk_id(doc_id, 12, 5),
            doc_id=doc_id,
            filename=filename,
            page_number=12,
            chunk_index=5,
            element_type=ElementType.TEXT,
            section_path="Article 18: Miscellaneous > 18.5 Governing Law and Jurisdiction",
            raw_content=(
                "Section 18.5 Governing Law and Jurisdiction: This Agreement shall be governed by and construed in accordance "
                "with the internal laws of the State of Delaware. Any legal action or proceeding arising under this Agreement "
                "shall be brought exclusively in the state or federal courts located in Wilmington, Delaware."
            ),
            contextualized_content=DocumentChunk.build_contextual_header(
                filename, 12, "Article 18: Miscellaneous > 18.5 Governing Law and Jurisdiction",
                "Section 18.5 Governing Law and Jurisdiction: This Agreement shall be governed by and construed in accordance "
                "with the internal laws of the State of Delaware. Any legal action or proceeding arising under this Agreement "
                "shall be brought exclusively in the state or federal courts located in Wilmington, Delaware."
            ),
            bounding_box=BoundingBox(l=50.0, t=400.0, r=520.0, b=480.0, page_number=12),
        ),
    ]

    index_manager.index_chunks(chunks)
    print(f"Indexed {len(chunks)} chunks into Chroma and BM25 stores successfully!")


if __name__ == "__main__":
    populate_sample_contract_index()

