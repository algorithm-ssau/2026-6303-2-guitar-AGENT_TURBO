#!/usr/bin/env python3
"""Проверка окружения для воспроизводимого запуска проекта."""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent


def print_status(level: str, message: str) -> None:
    """Печатает строку статуса в человекочитаемом виде."""
    print(f"[{level}] {message}")


def check_python_version(errors: list[str]) -> None:
    """Проверяет минимальную версию Python."""
    version = sys.version_info
    version_text = f"{version.major}.{version.minor}.{version.micro}"
    if version < (3, 9):
        errors.append(f"Python >= 3.9 required, found {version_text}")
        print_status("error", f"Python version: {version_text}")
        return
    print_status("ok", f"Python version: {version_text}")


def check_required_path(path: Path, label: str, errors: list[str], is_dir: bool = False) -> None:
    """Проверяет наличие обязательного файла или каталога."""
    exists = path.is_dir() if is_dir else path.is_file()
    if exists:
        suffix = "directory found" if is_dir else "found"
        print_status("ok", f"{label} {suffix}")
        return

    errors.append(f"Missing required {'directory' if is_dir else 'file'}: {path}")
    print_status("error", f"{label} missing")


def check_backend_import(errors: list[str]) -> None:
    """Проверяет импорт backend.main."""
    sys.path.insert(0, str(ROOT_DIR))
    try:
        importlib.import_module("backend.main")
    except Exception as exc:  # noqa: BLE001 - нужна явная причина для runbook-проверки
        errors.append(f"Cannot import backend.main: {exc}")
        print_status("error", f"backend.main import failed: {exc}")
        return
    print_status("ok", "backend.main imported")


def check_mock_mode(warnings: list[str]) -> None:
    """Проверяет переменную USE_MOCK_REVERB."""
    value = os.getenv("USE_MOCK_REVERB")
    if value:
        print_status("ok", f"USE_MOCK_REVERB is set to {value}")
        return

    warnings.append("USE_MOCK_REVERB is not set, default value will be used")
    print_status("ok", "USE_MOCK_REVERB is not set, default will be used")


def check_groq_key(warnings: list[str]) -> None:
    """Проверяет наличие GROQ_API_KEY без фатальной ошибки."""
    if os.getenv("GROQ_API_KEY"):
        print_status("ok", "GROQ_API_KEY is set")
        return

    warnings.append("GROQ_API_KEY is not set, degraded mode expected")
    print_status("warn", "GROQ_API_KEY is not set, degraded mode expected")


def main() -> int:
    """Точка входа скрипта."""
    os.chdir(ROOT_DIR)

    errors: list[str] = []
    warnings: list[str] = []

    check_python_version(errors)
    check_required_path(ROOT_DIR / "requirements.txt", "requirements.txt", errors)
    check_required_path(ROOT_DIR / ".env.example", ".env.example", errors)
    check_required_path(ROOT_DIR / "backend", "backend", errors, is_dir=True)

    if not errors:
        check_backend_import(errors)

    check_mock_mode(warnings)
    check_groq_key(warnings)

    if errors:
        print_status("error", "Environment check failed")
        return 1

    print_status("ok", "Environment check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
