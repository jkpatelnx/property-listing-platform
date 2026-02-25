from typing import Optional, List
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from models.property import Property
from models.property_image import PropertyImage
from schemas.property import PropertyCreate, PropertyUpdate


async def get_all_properties(
    db: AsyncSession,
    city: Optional[str] = None,
    min_price: Optional[Decimal] = None,
    max_price: Optional[Decimal] = None,
    skip: int = 0,
    limit: int = 200,
) -> List[Property]:
    filters = []
    if city:
        filters.append(Property.city.ilike(f"%{city}%"))
    if min_price is not None:
        filters.append(Property.price >= min_price)
    if max_price is not None:
        filters.append(Property.price <= max_price)

    query = (
        select(Property)
        .options(selectinload(Property.images))
        .order_by(Property.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    if filters:
        query = query.where(and_(*filters))

    result = await db.execute(query)
    return result.scalars().all()


async def get_property_by_id(db: AsyncSession, property_id: str) -> Optional[Property]:
    result = await db.execute(
        select(Property)
        .options(
            selectinload(Property.images),
            selectinload(Property.owner),
        )
        .where(Property.id == property_id)
    )
    return result.scalar_one_or_none()


async def create_property(
    db: AsyncSession, property_data: PropertyCreate, owner_id: str
) -> Property:
    prop = Property(
        **property_data.model_dump(),
        owner_id=owner_id,
    )
    db.add(prop)
    await db.flush()
    await db.refresh(prop)
    return prop


async def update_property(
    db: AsyncSession, property_id: str, property_data: PropertyUpdate, current_user_id: str
) -> Property:
    prop = await get_property_by_id(db, property_id)
    if not prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    if str(prop.owner_id) != str(current_user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    update_data = property_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(prop, key, value)

    await db.flush()
    await db.refresh(prop)
    return prop


async def delete_property(
    db: AsyncSession, property_id: str, current_user_id: str
) -> None:
    prop = await get_property_by_id(db, property_id)
    if not prop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Property not found")
    if str(prop.owner_id) != str(current_user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    await db.delete(prop)
    await db.flush()
