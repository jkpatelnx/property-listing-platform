from fastapi import APIRouter, Depends, status, Request, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from urllib.parse import urlencode

from database.session import get_db
from services.user_service import create_user, get_user_by_email
from services.auth_service import verify_password, create_access_token
from config.settings import settings
from schemas.user import UserCreate
from pydantic import ValidationError

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_cookie(response: RedirectResponse, token: str) -> RedirectResponse:
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
    )
    return response


@router.post("/register")
async def register(
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    # Validate inputs — re-render form with error instead of crashing
    try:
        user_data = UserCreate(email=email.strip(), password=password, full_name=full_name.strip())
    except ValidationError as exc:
        first_err = exc.errors()[0]["msg"]
        params = urlencode({"error": first_err, "name": full_name, "email": email})
        return RedirectResponse(url=f"/register?{params}", status_code=status.HTTP_303_SEE_OTHER)

    existing = await get_user_by_email(db, email.strip())
    if existing:
        params = urlencode({"error": "An account with this email already exists.", "name": full_name, "email": email})
        return RedirectResponse(url=f"/register?{params}", status_code=status.HTTP_303_SEE_OTHER)

    try:
        user = await create_user(db, user_data)
    except Exception:
        params = urlencode({"error": "Registration failed. Please try again.", "name": full_name, "email": email})
        return RedirectResponse(url=f"/register?{params}", status_code=status.HTTP_303_SEE_OTHER)

    token = create_access_token(data={"sub": str(user.id)})
    response = RedirectResponse(url="/properties", status_code=status.HTTP_303_SEE_OTHER)
    return _set_cookie(response, token)


@router.post("/login")
async def login(
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    error_params = urlencode({"error": "Invalid email or password. Please try again.", "email": email})

    try:
        user = await get_user_by_email(db, email.strip())
    except Exception:
        return RedirectResponse(url=f"/login?{error_params}", status_code=status.HTTP_303_SEE_OTHER)

    if not user or not verify_password(password, user.hashed_password):
        return RedirectResponse(url=f"/login?{error_params}", status_code=status.HTTP_303_SEE_OTHER)

    token = create_access_token(data={"sub": str(user.id)})
    redirect_url = "/admin" if user.role == "admin" else "/properties"
    response = RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    return _set_cookie(response, token)


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response
