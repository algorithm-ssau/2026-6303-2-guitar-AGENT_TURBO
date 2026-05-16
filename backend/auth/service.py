"""Сервис базовой авторизации пользователей."""

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import time
from typing import Optional, TypedDict

from fastapi import HTTPException, status

from backend.history.service import _get_connection
from backend.utils.logger import get_logger

logger = get_logger("auth")

LOGIN_PATTERN = re.compile(r"^[A-Za-z0-9_-]{3,32}$")
PASSWORD_MIN_LENGTH = 3
TOKEN_TTL_SECONDS = int(os.getenv("AUTH_TOKEN_TTL_SECONDS", str(60 * 60 * 24 * 7)))
_HASH_ITERATIONS = 120_000


class UserRecord(TypedDict):
    """Пользователь из SQLite."""

    id: int
    login: str


def init_auth_db() -> None:
    """Создать auth-таблицы и seeded admin/admin."""
    conn = _get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            login         TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
        );
    """)
    admin_id = seed_admin_user()
    try:
        conn.execute("UPDATE sessions SET user_id = ? WHERE user_id IS NULL", (admin_id,))
    except sqlite3.OperationalError as exc:
        if "no such column: user_id" not in str(exc).lower():
            raise
    conn.commit()
    logger.info("Auth БД инициализирована")


def seed_admin_user() -> int:
    """Создать или обновить тестового пользователя admin/admin."""
    conn = _get_connection()
    password_hash = hash_password("admin")
    conn.execute(
        "INSERT INTO users (login, password_hash) VALUES (?, ?) "
        "ON CONFLICT(login) DO UPDATE SET password_hash = excluded.password_hash",
        ("admin", password_hash),
    )
    row = conn.execute("SELECT id FROM users WHERE login = ?", ("admin",)).fetchone()
    if not row:
        raise RuntimeError("Не удалось создать seeded admin пользователя")
    return int(row["id"])


def validate_credentials(login: str, password: str) -> tuple[str, str]:
    """Нормализовать и проверить login/password."""
    normalized_login = login.strip()
    if not LOGIN_PATTERN.fullmatch(normalized_login):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Логин должен быть 3-32 символа: латинские буквы, цифры, _ или -.",
        )
    if len(password) < PASSWORD_MIN_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Пароль должен быть не короче 3 символов.",
        )
    return normalized_login, password


def register_user(login: str, password: str) -> tuple[str, UserRecord]:
    """Зарегистрировать пользователя и вернуть token."""
    login, password = validate_credentials(login, password)
    conn = _get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO users (login, password_hash) VALUES (?, ?)",
            (login, hash_password(password)),
        )
        conn.commit()
    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким логином уже существует.",
        ) from exc

    user = {"id": int(cursor.lastrowid), "login": login}
    return create_token(user), user


def authenticate_user(login: str, password: str) -> tuple[str, UserRecord]:
    """Проверить login/password и вернуть token."""
    login, password = validate_credentials(login, password)
    conn = _get_connection()
    row = conn.execute(
        "SELECT id, login, password_hash FROM users WHERE login = ?",
        (login,),
    ).fetchone()
    if not row or not verify_password(password, row["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль.",
        )

    user = {"id": int(row["id"]), "login": str(row["login"])}
    return create_token(user), user


def get_user_by_id(user_id: int) -> Optional[UserRecord]:
    """Получить пользователя по id."""
    conn = _get_connection()
    row = conn.execute("SELECT id, login FROM users WHERE id = ?", (user_id,)).fetchone()
    if not row:
        return None
    return {"id": int(row["id"]), "login": str(row["login"])}


def hash_password(password: str) -> str:
    """Сохранить пароль как PBKDF2 hash с salt."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        _HASH_ITERATIONS,
    )
    return "pbkdf2_sha256${}${}${}".format(
        _HASH_ITERATIONS,
        base64.urlsafe_b64encode(salt).decode("ascii"),
        base64.urlsafe_b64encode(digest).decode("ascii"),
    )


def verify_password(password: str, password_hash: str) -> bool:
    """Проверить пароль против PBKDF2 hash."""
    try:
        algorithm, iterations_raw, salt_raw, digest_raw = password_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(iterations_raw)
        salt = base64.urlsafe_b64decode(salt_raw.encode("ascii"))
        expected = base64.urlsafe_b64decode(digest_raw.encode("ascii"))
    except (ValueError, TypeError):
        return False

    actual = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations,
    )
    return hmac.compare_digest(actual, expected)


def create_token(user: UserRecord) -> str:
    """Создать простой HMAC-подписанный token."""
    payload = {
        "sub": user["id"],
        "login": user["login"],
        "exp": int(time.time()) + TOKEN_TTL_SECONDS,
    }
    payload_raw = _base64_json(payload)
    signature = _sign(payload_raw)
    return f"{payload_raw}.{signature}"


def verify_token(token: str) -> UserRecord:
    """Проверить token и вернуть пользователя."""
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Требуется авторизация.",
    )
    try:
        payload_raw, signature = token.split(".", 1)
    except ValueError as exc:
        raise credentials_error from exc

    expected_signature = _sign(payload_raw)
    if not hmac.compare_digest(signature, expected_signature):
        raise credentials_error

    try:
        payload = json.loads(_base64_decode(payload_raw))
    except (ValueError, json.JSONDecodeError) as exc:
        raise credentials_error from exc

    if int(payload.get("exp", 0)) < int(time.time()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Сессия истекла. Войдите снова.",
        )

    user_id = payload.get("sub")
    if not isinstance(user_id, int):
        raise credentials_error

    user = get_user_by_id(user_id)
    if not user:
        raise credentials_error
    return user


def _base64_json(payload: dict) -> str:
    raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _base64_decode(value: str) -> str:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii")).decode("utf-8")


def _sign(payload_raw: str) -> str:
    digest = hmac.new(
        _auth_secret(),
        payload_raw.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def _auth_secret() -> bytes:
    secret = os.getenv("AUTH_SECRET_KEY")
    if not secret:
        secret = "dev-only-change-me"
    return secret.encode("utf-8")
