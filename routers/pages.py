from fastapi import APIRouter, Depends, Request, Form, Query, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from typing import Optional, List
from decimal import Decimal, InvalidOperation
from urllib.parse import urlencode
from pydantic import ValidationError

from database.session import get_db
from services.auth_service import get_current_user, get_current_user_optional
from services.property_service import (
    get_all_properties, get_property_by_id, create_property, update_property, delete_property,
)
from services.image_service import add_images_to_property, replace_all_images, IMAGE_LABELS
from services.contact_service import create_contact_request
from schemas.property import PropertyCreate, PropertyUpdate
from models.user import User
from fastapi import HTTPException

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="templates")


def _to_decimal(val: Optional[str]) -> Optional[Decimal]:
    if not val or val.strip() == "":
        return None
    try:
        return Decimal(val)
    except InvalidOperation:
        return None


# ── Home ─────────────────────────────────────────────────────────────────────
@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return RedirectResponse(url="/properties")


# ── Auth Pages ────────────────────────────────────────────────────────────────
@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    error: Optional[str] = Query(default=None),
    email: Optional[str] = Query(default=None),
):
    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": error,
        "prefill_email": email or "",
    })


@router.get("/register", response_class=HTMLResponse)
async def register_page(
    request: Request,
    error: Optional[str] = Query(default=None),
    email: Optional[str] = Query(default=None),
    name: Optional[str] = Query(default=None),
):
    return templates.TemplateResponse("register.html", {
        "request": request,
        "error": error,
        "prefill_email": email or "",
        "prefill_name": name or "",
    })


# ── Property Pages ────────────────────────────────────────────────────────────
@router.get("/properties", response_class=HTMLResponse)
async def properties_list_page(
    request: Request,
    city: Optional[str] = None,
    min_price: Optional[str] = Query(default=None),
    max_price: Optional[str] = Query(default=None),
    property_type: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    min_p = _to_decimal(min_price)
    max_p = _to_decimal(max_price)
    properties = await get_all_properties(db, city=city or None, min_price=min_p, max_price=max_p)
    if property_type:
        properties = [p for p in properties if p.property_type == property_type]
    return templates.TemplateResponse(
        "properties/list.html",
        {
            "request": request,
            "properties": properties,
            "current_user": current_user,
            "filters": {"city": city, "min_price": min_price, "max_price": max_price, "property_type": property_type},
        },
    )


@router.get("/properties/create", response_class=HTMLResponse)
async def create_property_page(
    request: Request,
    error: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_user),
):
    return templates.TemplateResponse(
        "properties/create.html",
        {"request": request, "current_user": current_user, "image_labels": IMAGE_LABELS, "error": error},
    )


@router.post("/properties/create", response_class=HTMLResponse)
async def create_property_form(
    request: Request,
    title: str = Form(...),
    description: Optional[str] = Form(None),
    city: str = Form(...),
    address: str = Form(...),
    price: Decimal = Form(...),
    bedrooms: int = Form(1),
    bathrooms: int = Form(1),
    property_type: str = Form("apartment"),
    listing_type: str = Form("sale"),
    # 6 labeled image slots
    image_0: Optional[UploadFile] = File(None),
    image_1: Optional[UploadFile] = File(None),
    image_2: Optional[UploadFile] = File(None),
    image_3: Optional[UploadFile] = File(None),
    image_4: Optional[UploadFile] = File(None),
    image_5: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not image_0 or not image_0.filename:
        params = urlencode({"error": "Please upload at least one photo (Exterior)."})
        return RedirectResponse(url=f"/properties/create?{params}", status_code=status.HTTP_303_SEE_OTHER)

    try:
        data = PropertyCreate(
            title=title, description=description, city=city, address=address,
            price=price, bedrooms=bedrooms, bathrooms=bathrooms, property_type=property_type,
        )
        prop = await create_property(db, data, owner_id=str(current_user.id))
    except (ValidationError, Exception) as e:
        err = str(e.errors()[0]['msg']) if isinstance(e, ValidationError) else "Failed to create property. Check your inputs."
        params = urlencode({"error": err})
        return RedirectResponse(url=f"/properties/create?{params}", status_code=status.HTTP_303_SEE_OTHER)

    uploads = [image_0, image_1, image_2, image_3, image_4, image_5]
    saved = await add_images_to_property(db, str(prop.id), uploads, IMAGE_LABELS)
    if saved:
        prop.image_filename = saved[0].filename
        await db.flush()

    return RedirectResponse(url=f"/properties/{prop.id}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/properties/{property_id}", response_class=HTMLResponse)
async def property_detail_page(
    request: Request,
    property_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    prop = await get_property_by_id(db, property_id)
    if not prop:
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
    return templates.TemplateResponse(
        "properties/detail.html",
        {"request": request, "property": prop, "current_user": current_user},
    )


@router.post("/properties/{property_id}/contact")
async def submit_contact_request(
    request: Request,
    property_id: str,
    name: str = Form(...),
    email: str = Form(...),
    message: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prop = await get_property_by_id(db, property_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    await create_contact_request(
        db, property_id=str(prop.id), user_id=str(current_user.id),
        name=name, email=email, message=message,
    )
    return RedirectResponse(
        url=f"/properties/{property_id}?success=1",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.get("/properties/{property_id}/edit", response_class=HTMLResponse)
async def edit_property_page(
    request: Request,
    property_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prop = await get_property_by_id(db, property_id)
    if not prop or str(prop.owner_id) != str(current_user.id):
        return RedirectResponse(url="/properties", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        "properties/edit.html",
        {"request": request, "property": prop, "current_user": current_user, "image_labels": IMAGE_LABELS},
    )


@router.post("/properties/{property_id}/edit", response_class=HTMLResponse)
async def edit_property_form(
    request: Request,
    property_id: str,
    title: str = Form(...),
    description: Optional[str] = Form(None),
    city: str = Form(...),
    address: str = Form(...),
    price: Decimal = Form(...),
    bedrooms: int = Form(1),
    bathrooms: int = Form(1),
    property_type: str = Form("apartment"),
    listing_type: str = Form("sale"),
    # 6 labeled image slots
    image_0: Optional[UploadFile] = File(None),
    image_1: Optional[UploadFile] = File(None),
    image_2: Optional[UploadFile] = File(None),
    image_3: Optional[UploadFile] = File(None),
    image_4: Optional[UploadFile] = File(None),
    image_5: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = PropertyUpdate(
        title=title, description=description, city=city, address=address,
        price=price, bedrooms=bedrooms, bathrooms=bathrooms, property_type=property_type,
    )
    prop = await update_property(db, property_id, data, str(current_user.id))

    uploads = [image_0, image_1, image_2, image_3, image_4, image_5]
    has_new = any(u and u.filename for u in uploads)
    if has_new:
        saved = await replace_all_images(db, str(prop.id), uploads, IMAGE_LABELS)
        if saved:
            prop.image_filename = saved[0].filename
            await db.flush()

    return RedirectResponse(url=f"/properties/{property_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/properties/{property_id}/delete")
async def delete_property_form(
    request: Request,
    property_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await delete_property(db, property_id, str(current_user.id))
    return RedirectResponse(url="/properties", status_code=status.HTTP_303_SEE_OTHER)
