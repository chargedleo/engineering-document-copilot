#!/usr/bin/env python3
"""
Seed Data Script
Populates the PostgreSQL database with sample engineering documents and metadata for testing.
"""

import asyncio
import logging
import os
import sys

# Ensure backend directory is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.database import AsyncSessionLocal
from app.models.document import Document, CadMetadata, DocumentStatus

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


SAMPLE_DOCUMENTS = [
    {
        "filename": "Aero_Turbine_Blade_Specs_v2.1.pdf",
        "document_type": "SPECIFICATION",
        "part_number": "TB-100-A",
        "revision": "2.1",
        "file_path": "data/documents/Aero_Turbine_Blade_Specs_v2.1.pdf",
        "mime_type": "application/pdf",
        "file_size_bytes": 1048576,
        "status": DocumentStatus.COMPLETED,
        "metadata_payload": {
            "title": "Aero Turbine Blade Material and Thermal Specs",
            "author": "Propulsion Engineering Group",
            "version": "2.1",
            "tags": ["aerospace", "materials", "turbines", "nickel-alloy"]
        }
    },
    {
        "filename": "Turbine_Shaft_Assembly_RevC.step",
        "document_type": "DRAWING",
        "part_number": "TS-402-C",
        "revision": "C",
        "file_path": "data/documents/Turbine_Shaft_Assembly_RevC.step",
        "mime_type": "application/step",
        "file_size_bytes": 4518920,
        "status": DocumentStatus.COMPLETED,
        "metadata_payload": {
            "assembly_name": "Turbine Shaft Main Assembly",
            "cad_software": "Siemens NX",
            "units": "mm"
        }
    }
]


async def seed_data():
    logger.info("Connecting to database for seeding...")
    async with AsyncSessionLocal() as session:
        for doc_data in SAMPLE_DOCUMENTS:
            doc = Document(
                filename=doc_data["filename"],
                document_type=doc_data["document_type"],
                part_number=doc_data["part_number"],
                revision=doc_data["revision"],
                file_path=doc_data["file_path"],
                mime_type=doc_data["mime_type"],
                file_size_bytes=doc_data["file_size_bytes"],
                status=doc_data["status"],
                metadata_payload=doc_data["metadata_payload"]
            )
            session.add(doc)
            await session.flush()

            if doc_data["part_number"] == "TS-402-C":
                cad_meta = CadMetadata(
                    document_id=doc.id,
                    part_number="TS-402-C",
                    part_name="High-Pressure Turbine Rotor Shaft",
                    material="Inconel 718",
                    mass_kg=14.85,
                    volume_cm3=1810.97,
                    bounding_box_dimensions={"length_mm": 420.0, "diameter_mm": 85.0},
                    attributes={
                        "tolerance_class": "ISO 2768-m",
                        "surface_finish_ra_um": 0.8,
                        "critical_feature": "spline_engagement_teeth"
                    }
                )
                session.add(cad_meta)

        await session.commit()
    logger.info("Sample engineering data seeded successfully.")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(seed_data())
    except Exception as e:
        logger.error(f"Failed to seed data: {e}")
        sys.exit(1)
