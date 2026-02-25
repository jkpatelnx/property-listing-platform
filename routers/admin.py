from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from starlette import status

from database.session import get_db
from services.auth_service import require_admin
from services.property_service import get_all_properties, get_property_by_id, delete_property
from services.contact_service import get_all_requests, set_request_status, count_pending_requests
from models.user import User
from models.property import Property
from models.contact_request import ContactRequest

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="templates")


# ── Dashboard ─────────────────────────────────────────────────────────────────
@router.get("", response_class=HTMLResponse)
async def admin_dashboard(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    total_properties = (await db.execute(select(func.count()).select_from(Property))).scalar_one()
    total_users = (await db.execute(select(func.count()).select_from(User))).scalar_one()
    pending_requests = await count_pending_requests(db)
    total_requests = (await db.execute(select(func.count()).select_from(ContactRequest))).scalar_one()
    recent_properties = await get_all_properties(db, limit=5)
    recent_requests = await get_all_requests(db)
    recent_requests = recent_requests[:5]

    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "current_user": current_user,
            "stats": {
                "total_properties": total_properties,
                "total_users": total_users,
                "pending_requests": pending_requests,
                "total_requests": total_requests,
            },
            "recent_properties": recent_properties,
            "recent_requests": recent_requests,
        },
    )


# ── Properties Management ─────────────────────────────────────────────────────
@router.get("/properties", response_class=HTMLResponse)
async def admin_properties(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    properties = await get_all_properties(db, limit=200)
    return templates.TemplateResponse(
        "admin/properties.html",
        {"request": request, "current_user": current_user, "properties": properties},
    )


@router.post("/properties/{property_id}/delete")
async def admin_delete_property(
    property_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Admin can delete any property regardless of owner."""
    prop = await get_property_by_id(db, property_id)
    if prop:
        await db.delete(prop)
        await db.flush()
    return RedirectResponse(url="/admin/properties", status_code=status.HTTP_303_SEE_OTHER)


# ── Contact Requests Management ───────────────────────────────────────────────
@router.get("/requests", response_class=HTMLResponse)
async def admin_requests(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    requests = await get_all_requests(db)
    return templates.TemplateResponse(
        "admin/requests.html",
        {"request": request, "current_user": current_user, "contact_requests": requests},
    )


@router.post("/requests/{request_id}/handle")
async def admin_handle_request(
    request_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    await set_request_status(db, request_id, "handled")
    return RedirectResponse(url="/admin/requests", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/requests/{request_id}/reopen")
async def admin_reopen_request(
    request_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    await set_request_status(db, request_id, "pending")
    return RedirectResponse(url="/admin/requests", status_code=status.HTTP_303_SEE_OTHER)
