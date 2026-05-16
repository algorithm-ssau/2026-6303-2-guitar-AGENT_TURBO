"""Pydantic-модели для auth API."""

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel

from backend.auth.service import LOGIN_PATTERN


class AuthCredentials(BaseModel):
    """Логин и пароль пользователя."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    login: str = Field(..., min_length=3, max_length=32)
    password: str = Field(..., min_length=3, max_length=128)

    @field_validator("login")
    @classmethod
    def validate_login(cls, value: str) -> str:
        login = value.strip()
        if not LOGIN_PATTERN.fullmatch(login):
            raise ValueError("Логин может содержать только латинские буквы, цифры, _ и -")
        return login


class AuthUser(BaseModel):
    """Публичные данные текущего пользователя."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    id: int
    login: str


class AuthResponse(BaseModel):
    """Ответ успешной регистрации или входа."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)

    token: str
    user: AuthUser
