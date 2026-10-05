from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict


class BoundingBox(BaseModel):
    min_x: Optional[float] = None
    min_y: Optional[float] = None
    min_z: Optional[float] = None
    max_x: Optional[float] = None
    max_y: Optional[float] = None
    max_z: Optional[float] = None
    length_mm: Optional[float] = None
    width_mm: Optional[float] = None
    height_mm: Optional[float] = None
    diameter_mm: Optional[float] = None


class CadMetadataBase(BaseModel):
    part_number: Optional[str] = None
    part_name: Optional[str] = None
    material: Optional[str] = None
    mass_kg: Optional[float] = None
    volume_cm3: Optional[float] = None
    bounding_box_dimensions: Optional[Dict[str, Any]] = None
    attributes: Optional[Dict[str, Any]] = None


class CadMetadataCreate(CadMetadataBase):
    document_id: str


class CadMetadataResponse(CadMetadataBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    document_id: str
    created_at: datetime
    updated_at: datetime


class CadFilter(BaseModel):
    material: Optional[str] = None
    part_number: Optional[str] = None
    search_query: Optional[str] = None
