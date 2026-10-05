from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.document import CadMetadata
from app.schemas.cad import CadMetadataCreate, CadFilter


class CadService:
    @staticmethod
    async def list_cad_metadata(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 50,
        filter_params: Optional[CadFilter] = None
    ) -> tuple[List[CadMetadata], int]:
        query = select(CadMetadata)

        if filter_params:
            if filter_params.part_number:
                query = query.where(CadMetadata.part_number.ilike(f"%{filter_params.part_number}%"))
            if filter_params.material:
                query = query.where(CadMetadata.material.ilike(f"%{filter_params.material}%"))
            if filter_params.search_query:
                query = query.where(
                    (CadMetadata.part_name.ilike(f"%{filter_params.search_query}%")) |
                    (CadMetadata.part_number.ilike(f"%{filter_params.search_query}%"))
                )

        count_query = select(func.count()).select_from(query.subquery())
        total = await db.scalar(count_query) or 0

        query = query.order_by(CadMetadata.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        cad_records = list(result.scalars().all())

        return cad_records, total

    @staticmethod
    async def get_cad_metadata_by_id(db: AsyncSession, cad_id: str) -> Optional[CadMetadata]:
        query = select(CadMetadata).where(CadMetadata.id == cad_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_cad_by_document_id(db: AsyncSession, document_id: str) -> List[CadMetadata]:
        query = select(CadMetadata).where(CadMetadata.document_id == document_id)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def create_cad_metadata(db: AsyncSession, cad_in: CadMetadataCreate) -> CadMetadata:
        cad_record = CadMetadata(
            document_id=cad_in.document_id,
            part_number=cad_in.part_number,
            part_name=cad_in.part_name,
            material=cad_in.material,
            mass_kg=cad_in.mass_kg,
            volume_cm3=cad_in.volume_cm3,
            bounding_box_dimensions=cad_in.bounding_box_dimensions,
            attributes=cad_in.attributes,
        )
        db.add(cad_record)
        await db.commit()
        await db.refresh(cad_record)
        return cad_record
