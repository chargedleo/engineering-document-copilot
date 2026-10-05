import logging
from typing import Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document

logger = logging.getLogger("engineering_copilot.agents.tools.metadata")


class GetDocumentMetadataTool:
    """
    Tool retrieving verified metadata for engineering documents from PostgreSQL.
    Returns document ID, filename, document type, part number, revision, status,
    page count, file size, and creation timestamp.
    """
    name: str = "get_document_metadata"
    description: str = (
        "Retrieve verified metadata for a specific engineering document from the database. "
        "Use this tool when answering questions about document revision, status, page count, "
        "part number, or file properties."
    )

    @classmethod
    async def run(
        cls,
        db: AsyncSession,
        document_id: Optional[str] = None,
        part_number: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Query PostgreSQL document registry for document metadata."""
        if not document_id and not part_number and not filename:
            return {
                "success": False,
                "found": False,
                "error": "At least one search parameter (document_id, part_number, or filename) must be provided.",
            }

        try:
            stmt = select(Document).options(selectinload(Document.pages))

            if document_id:
                stmt = stmt.where(Document.id == document_id.strip())
            elif part_number:
                stmt = stmt.where(Document.part_number == part_number.strip())
            elif filename:
                stmt = stmt.where(Document.filename == filename.strip())

            result = await db.execute(stmt)
            doc = result.scalars().first()

            if not doc:
                identifier = document_id or part_number or filename
                return {
                    "success": True,
                    "found": False,
                    "message": f"No engineering document found matching identifier '{identifier}'.",
                }

            page_count = len(doc.pages) if doc.pages else 0
            status_str = doc.status.value if hasattr(doc.status, "value") else str(doc.status)

            return {
                "success": True,
                "found": True,
                "document_id": doc.id,
                "filename": doc.filename,
                "document_type": doc.document_type,
                "part_number": doc.part_number,
                "revision": doc.revision,
                "status": status_str,
                "page_count": page_count,
                "file_size_bytes": doc.file_size_bytes,
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
            }
        except Exception as e:
            logger.error(f"Error in get_document_metadata tool: {e}", exc_info=True)
            return {
                "success": False,
                "found": False,
                "error": f"Database query failed: {str(e)}",
            }
