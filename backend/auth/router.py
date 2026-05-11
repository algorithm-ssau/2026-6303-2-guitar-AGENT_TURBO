"""REST-эндпоинты авторизации."""

from fastapi import APIRouter, Depends

from backend.auth.dependencies import get_current_user
from backend.auth.models import AuthCredentials, AuthResponse, AuthUser
from backend.auth.service import UserRecord, authenticate_user, register_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse)
async def register(credentials: AuthCredentials) -> AuthResponse:
    """Зарегистрировать пользователя по login/password."""
    token, user = register_user(credentials.login, credentials.password)
    return AuthResponse(token=token, user=AuthUser(**user))


@router.post("/login", response_model=AuthResponse)
async def login(credentials: AuthCredentials) -> AuthResponse:
    """Войти по login/password."""
    token, user = authenticate_user(credentials.login, credentials.password)
    return AuthResponse(token=token, user=AuthUser(**user))


@router.get("/me", response_model=AuthUser)
async def me(current_user: UserRecord = Depends(get_current_user)) -> AuthUser:
    """Вернуть текущего пользователя."""
    return AuthUser(**current_user)
