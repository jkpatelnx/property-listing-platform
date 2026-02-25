from typing import Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import get_db
from schemas.property import PropertyCreate, PropertyUpdate, PropertyResponse
from services.property_service import (
    get_all_properties,
    get_property_by_id,
    create_property,
    update_property,
    delete_property,
)
from services.auth_service import get_current_user
from models.user import User

router = APIRouter(prefix="/api/properties", tags=["properties"])


@router.get("/", response_model=list[PropertyResponse])
async def list_properties(
    city: Optional[str] = None,
    min_price: Optional[Decimal] = None,
    max_price: Optional[Decimal] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    return await get_all_properties(db, city=city, min_price=min_price, max_price=max_price, skip=skip, limit=limit)


@router.get("/{property_id}", response_model=PropertyResponse)
async def get_property(property_id: str, db: AsyncSession = Depends(get_db)):
    prop = await get_property_by_id(db, property_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    return prop


@router.post("/", response_model=PropertyResponse, status_code=status.HTTP_201_CREATED)
async def create_property_api(
    property_data: PropertyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await create_property(db, property_data, owner_id=str(current_user.id))


@router.put("/{property_id}", response_model=PropertyResponse)
async def update_property_api(
    property_id: str,
    property_data: PropertyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await update_property(db, property_id, property_data, str(current_user.id))


@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_property_api(
    property_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await delete_property(db, property_id, str(current_user.id))
