"""
Image service: save up to 6 labeled images per property, delete, reorder.
"""
import os
import uuid as uuid_lib
import shutil
from typing import Optional, List
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from models.property_image import PropertyImage

UPLOAD_DIR = "static/uploads"
ALLOWED_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
IMAGE_LABELS = ["Exterior", "Living Room", "Kitchen", "Bedroom", "Bathroom", "View"]
MAX_IMAGES = 6


def _ext(filename: str) -> str:
    return os.path.splitext(filename)[1].lower()


def _to_uuid(val: str):
    """Convert string UUID to uuid.UUID object for SQLAlchemy UUID column."""
    if isinstance(val, uuid_lib.UUID):
        return val
    return uuid_lib.UUID(str(val))


async def save_image_file(upload: UploadFile) -> Optional[str]:
    """Save a single UploadFile to disk. Returns filename or None on error/empty."""
    try:
        if not upload or not upload.filename or upload.filename == "":
            return None
        ext = _ext(upload.filename)
        if ext not in ALLOWED_EXTS:
            return None
        # Ensure upload directory exists
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        filename = f"{uuid_lib.uuid4().hex}{ext}"
        dest = os.path.join(UPLOAD_DIR, filename)
        # Reset file cursor to beginning before reading
        await upload.seek(0)
        contents = await upload.read()
        if not contents:
            return None
        with open(dest, "wb") as f:
            f.write(contents)
        return filename
    except Exception:
        return None


async def add_images_to_property(
    db: AsyncSession,
    property_id: str,
    uploads: List[Optional[UploadFile]],
    labels: List[str],
) -> List[PropertyImage]:
    """
    Save uploaded files and add PropertyImage rows.
    Respects MAX_IMAGES cap across existing + new images.
    Returns newly created PropertyImage objects.
    """
    pid = _to_uuid(property_id)

    result = await db.execute(
        select(PropertyImage).where(PropertyImage.property_id == pid)
    )
    existing = result.scalars().all()
    current_max_order = max((img.display_order for img in existing), default=-1)

    created = []
    for i, (upload, label) in enumerate(zip(uploads, labels)):
        if len(existing) + len(created) >= MAX_IMAGES:
            break
        filename = await save_image_file(upload)
        if not filename:
            continue
        img = PropertyImage(
            property_id=pid,
            filename=filename,
            label=label,
            display_order=current_max_order + 1 + i,
        )
        db.add(img)
        created.append(img)

    if created:
        await db.flush()
    return created


async def replace_all_images(
    db: AsyncSession,
    property_id: str,
    uploads: List[Optional[UploadFile]],
    labels: List[str],
) -> List[PropertyImage]:
    """
    Delete all existing images for a property and add new ones.
    """
    pid = _to_uuid(property_id)
    await db.execute(
        delete(PropertyImage).where(PropertyImage.property_id == pid)
    )
    await db.flush()

    created = []
    for i, (upload, label) in enumerate(zip(uploads, labels)):
        if i >= MAX_IMAGES:
            break
        filename = await save_image_file(upload)
        if not filename:
            continue
        img = PropertyImage(
            property_id=pid,
            filename=filename,
            label=label,
            display_order=i,
        )
        db.add(img)
        created.append(img)

    if created:
        await db.flush()
    return created


async def seed_images_for_property(
    db: AsyncSession,
    property_id: str,
    image_specs: List[dict],  # [{"filename": "...", "label": "..."}, ...]
) -> None:
    """Directly insert PropertyImage rows using existing filenames (for seeding)."""
    pid = _to_uuid(property_id)
    for i, spec in enumerate(image_specs[:MAX_IMAGES]):
        img = PropertyImage(
            property_id=pid,
            filename=spec["filename"],
            label=spec["label"],
            display_order=i,
        )
        db.add(img)
