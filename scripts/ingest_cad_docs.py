#!/usr/bin/env python3
"""
Document & CAD Ingestion CLI Script
Scans data/documents/ or a specified input path, parses engineering documents
and CAD models, extracts metadata, and prepares data for search indexing.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("ingest-cad-docs")


def scan_input_directory(target_path: Path):
    """Scan the target path for engineering documents and CAD files."""
    supported_extensions = {
        ".pdf": "PDF Document",
        ".docx": "Word Document",
        ".txt": "Text Spec",
        ".md": "Markdown Spec",
        ".xlsx": "BOM Spreadsheet",
        ".step": "3D CAD (STEP)",
        ".stp": "3D CAD (STEP)",
        ".iges": "3D CAD (IGES)",
        ".igs": "3D CAD (IGES)",
        ".dxf": "2D CAD (DXF)",
        ".dwg": "2D CAD (DWG)",
        ".stl": "3D Mesh (STL)",
    }

    found_files = []
    if not target_path.exists():
        logger.error(f"Path does not exist: {target_path}")
        return found_files

    for file_path in target_path.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
            found_files.append((file_path, supported_extensions[file_path.suffix.lower()]))

    return found_files


def process_file(file_path: Path, file_type: str, dry_run: bool = False):
    """
    Placeholder parsing step for engineering documents and CAD models.
    (Future integration will use CAD kernel APIs and document intelligence extractors)
    """
    logger.info(f"Processing: {file_path.name} [{file_type}]")
    if dry_run:
        logger.info(f"Dry run: Skipping parsing and indexing for {file_path.name}")
        return

    # In production, this will trigger CAD parsing, text extraction, chunking, and embedding
    logger.info(f"Successfully staged {file_path.name} for downstream extraction.")


def main():
    parser = argparse.ArgumentParser(
        description="Engineering Document Intelligence & CAD Ingestion CLI"
    )
    parser.add_argument(
        "--source-dir",
        type=str,
        default="data/documents",
        help="Directory containing engineering documents and CAD models to ingest."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Scan and list files without parsing or storing."
    )
    args = parser.parse_args()

    source_path = Path(args.source_dir).resolve()
    logger.info(f"Starting ingestion scan on: {source_path}")

    files = scan_input_directory(source_path)
    logger.info(f"Found {len(files)} candidate engineering files.")

    for file_path, file_type in files:
        process_file(file_path, file_type, dry_run=args.dry_run)

    logger.info("Ingestion scan complete.")


if __name__ == "__main__":
    main()
