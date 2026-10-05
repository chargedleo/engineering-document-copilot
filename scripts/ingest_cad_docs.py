#!/usr/bin/env python3
"""
Document Ingestion CLI Script
Ingests engineering PDF documents into PostgreSQL, extracts text page-by-page
using PyMuPDF with OpenCV + Tesseract OCR fallback, and reports extraction statistics.
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

# Add backend directory to path to allow importing app modules
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Ensure Windows Selector event loop policy for asyncpg
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.core.database import AsyncSessionLocal
from app.services.document_service import DocumentService
from app.services.document_processing.pdf_extractor import PDFValidationError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("ingest-docs")


async def ingest_single_pdf(
    file_path: Path,
    document_type: str = "SPECIFICATION",
    part_number: str = None,
    revision: str = "A",
    chunk: bool = True
):
    """Ingest, process, and optionally chunk a single PDF file."""
    if not file_path.is_file():
        logger.error(f"File not found: {file_path}")
        return False

    if not file_path.suffix.lower() == ".pdf":
        logger.error(f"Unsupported file format ({file_path.suffix}). Only PDF files are supported.")
        return False

    logger.info(f"Ingesting PDF: {file_path.name} ({file_path.stat().st_size} bytes)")

    with open(file_path, "rb") as f:
        file_bytes = f.read()

    async with AsyncSessionLocal() as session:
        try:
            doc, result = await DocumentService.process_and_store_document(
                db=session,
                file_bytes=file_bytes,
                original_filename=file_path.name,
                document_type=document_type,
                part_number=part_number,
                revision=revision,
            )

            chunk_info = None
            if chunk:
                logger.info(f"Generating structural chunks and embeddings for document {doc.id}...")
                chunk_info = await DocumentService.generate_document_chunks(session, doc.id)

            print("\n" + "=" * 60)
            print("  DOCUMENT INGESTION & INDEXING REPORT")
            print("=" * 60)
            print(f"  Document ID       : {doc.id}")
            print(f"  Filename          : {doc.filename}")
            print(f"  Document Type     : {doc.document_type}")
            print(f"  Part Number       : {doc.part_number or 'N/A'}")
            print(f"  Revision          : {doc.revision}")
            print(f"  Total Pages       : {result.total_pages}")
            print(f"  Processed Pages   : {result.processed_pages}")
            print(f"  Native Text Pages : {result.total_pages - result.ocr_pages}")
            print(f"  OCR Pages         : {result.ocr_pages}")
            print(f"  Document Status   : {doc.status}")
            if chunk_info:
                print(f"  Chunks Created    : {chunk_info.chunks_created}")
                print(f"  Embeddings Made   : {chunk_info.embeddings_generated}")
                print(f"  Indexed into Search: {chunk_info.indexed_count}")
                print(f"  Indexing Status   : {chunk_info.status}")
            print("=" * 60 + "\n")
            return True

        except PDFValidationError as e:
            logger.error(f"Validation failure for {file_path.name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to process {file_path.name}: {e}")
            return False


async def ingest_directory(dir_path: Path, document_type: str = "SPECIFICATION", chunk: bool = True):
    """Scan directory and ingest all candidate PDF documents."""
    pdf_files = list(dir_path.glob("*.pdf")) + list(dir_path.glob("*.PDF"))
    if not pdf_files:
        logger.warning(f"No PDF documents found in: {dir_path}")
        return

    logger.info(f"Found {len(pdf_files)} PDF documents to ingest.")
    success_count = 0
    for pdf_file in pdf_files:
        if await ingest_single_pdf(pdf_file, document_type=document_type, chunk=chunk):
            success_count += 1

    logger.info(f"Ingestion batch completed: {success_count}/{len(pdf_files)} succeeded.")


def main():
    parser = argparse.ArgumentParser(
        description="Engineering Document Intelligence Ingestion & Chunking CLI"
    )
    parser.add_argument(
        "file",
        nargs="?",
        default=None,
        type=str,
        help="Path to a single engineering PDF to ingest."
    )
    parser.add_argument(
        "--source-dir",
        type=str,
        default=None,
        help="Directory containing engineering PDFs to ingest (e.g. data/documents)."
    )
    parser.add_argument(
        "--document-type",
        type=str,
        default="SPECIFICATION",
        help="Document type (SPECIFICATION, MANUAL, DATASHEET, DRAWING, BOM)."
    )
    parser.add_argument(
        "--part-number",
        type=str,
        default=None,
        help="Optional engineering part or assembly number."
    )
    parser.add_argument(
        "--revision",
        type=str,
        default="A",
        help="Engineering revision identifier (default: A)."
    )
    parser.add_argument(
        "--no-chunk",
        dest="chunk",
        action="store_false",
        help="Skip chunk generation and vector indexing after ingestion."
    )
    parser.set_defaults(chunk=True)

    args = parser.parse_args()

    if args.file:
        file_path = Path(args.file).resolve()
        asyncio.run(ingest_single_pdf(
            file_path,
            document_type=args.document_type,
            part_number=args.part_number,
            revision=args.revision,
            chunk=args.chunk,
        ))
    elif args.source_dir:
        dir_path = Path(args.source_dir).resolve()
        asyncio.run(ingest_directory(dir_path, document_type=args.document_type, chunk=args.chunk))
    else:
        # Default scan data/documents/
        default_dir = ROOT_DIR / "data" / "documents"
        logger.info(f"No specific file provided. Scanning default directory: {default_dir}")
        asyncio.run(ingest_directory(default_dir, document_type=args.document_type, chunk=args.chunk))


if __name__ == "__main__":
    main()

