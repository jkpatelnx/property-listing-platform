from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status

from models.contact_request import ContactRequest


async def create_contact_request(
    db: AsyncSession,
    property_id: str,
    user_id: str,
    name: str,
    email: str,
    message: str,
) -> ContactRequest:
    req = ContactRequest(
        property_id=property_id,
        user_id=user_id,
        name=name,
        email=email,
        message=message,
        status="pending",
    )
    db.add(req)
    await db.flush()
    await db.refresh(req)
    return req


async def get_all_requests(
    db: AsyncSession,
    property_id: Optional[str] = None,
) -> List[ContactRequest]:
    query = (
        select(ContactRequest)
        .options(selectinload(ContactRequest.property), selectinload(ContactRequest.user))
        .order_by(ContactRequest.created_at.desc())
    )
    if property_id:
        query = query.where(ContactRequest.property_id == property_id)
    result = await db.execute(query)
    return result.scalars().all()


async def count_pending_requests(db: AsyncSession) -> int:
    result = await db.execute(
        select(func.count()).where(ContactRequest.status == "pending")
    )
    return result.scalar_one()


async def set_request_status(
    db: AsyncSession,
    request_id: str,
    new_status: str,
) -> ContactRequest:
    result = await db.execute(
        select(ContactRequest).where(ContactRequest.id == request_id)
    )
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    req.status = new_status
    await db.flush()
    await db.refresh(req)
    return req
