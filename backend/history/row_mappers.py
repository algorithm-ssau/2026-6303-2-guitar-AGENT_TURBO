"""Преобразование SQLite rows истории в dict-структуры API."""

import json
import sqlite3


def session_row_to_dict(row: sqlite3.Row) -> dict:
    return dict(row)


def message_row_to_dict(row: sqlite3.Row) -> dict:
    item = dict(row)
    if item["results"]:
        item["results"] = json.loads(item["results"])
    if item.get("search_params"):
        item["search_params"] = json.loads(item["search_params"])
    else:
        item["search_params"] = None
    return item


def session_state_row_to_dict(row: sqlite3.Row) -> dict:
    if not row:
        return {}
    try:
        data = json.loads(row[0])
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}
