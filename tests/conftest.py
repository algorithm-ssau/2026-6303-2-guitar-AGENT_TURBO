"""
Конфигурация pytest для тестов.
"""
import sys
from pathlib import Path

# Добавляем корень проекта в sys.path для импортов
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))


def auth_token(client):
    response = client.post("/api/auth/login", json={"login": "admin", "password": "admin"})
    assert response.status_code == 200
    return response.json()["token"]


def auth_headers(client):
    return {"Authorization": f"Bearer {auth_token(client)}"}


def auth_ws_path(client, path="/chat"):
    return f"{path}?token={auth_token(client)}"
