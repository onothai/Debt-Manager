from __future__ import annotations

import os
from typing import Any

import httpx

import app_config

# URL ฐานมาจาก .env: API_BASE_URL หรือ UVICORN_HOST + UVICORN_PORT (ดู app_config.py)
# มือถือเปิดแค่เว็บ Flet — httpx ทำงานที่เครื่องรัน Python
# ถ้า DB ช้า/ค้าง: $env:API_HTTP_TIMEOUT = '120'


def _api_base() -> str:
    return app_config.client_api_base_url()


def _http_timeout() -> httpx.Timeout:
    try:
        total = float(os.environ.get("API_HTTP_TIMEOUT", "90"))
    except ValueError:
        total = 90.0
    total = max(15.0, min(total, 300.0))
    connect = min(45.0, max(10.0, total / 3))
    return httpx.Timeout(connect=connect, read=total, write=total, pool=total)


def get_users() -> list[dict]:
    with httpx.Client(timeout=_http_timeout()) as client:
        response = client.get(f"{_api_base()}/users")
        response.raise_for_status()
        return response.json()


def get_user(user_id: int) -> dict:
    with httpx.Client(timeout=_http_timeout()) as client:
        response = client.get(f"{_api_base()}/users/{user_id}")
        response.raise_for_status()
        return response.json()


def create_user(username: str, password: str) -> dict:
    payload = {"username": username, "password": password, "debt_total": 0}
    with httpx.Client(timeout=_http_timeout()) as client:
        response = client.post(f"{_api_base()}/users", json=payload)
        response.raise_for_status()
        return response.json()


def update_user_debt_total(user_id: int, debt_total: float) -> dict:
    payload = {"debt_total": debt_total}
    with httpx.Client(timeout=_http_timeout()) as client:
        response = client.put(f"{_api_base()}/users/{user_id}", json=payload)
        response.raise_for_status()
        return response.json()


def delete_user(user_id: int) -> None:
    with httpx.Client(timeout=_http_timeout()) as client:
        response = client.delete(f"{_api_base()}/users/{user_id}")
        response.raise_for_status()


def list_debts(user_id: int | None = None, status: str | None = None) -> list[dict]:
    params: dict[str, Any] = {}
    if user_id is not None:
        params["user_id"] = user_id
    if status is not None:
        params["status"] = status
    with httpx.Client(timeout=_http_timeout()) as client:
        response = client.get(f"{_api_base()}/debts", params=params)
        response.raise_for_status()
        return response.json()


def get_debt(debt_id: int) -> dict:
    with httpx.Client(timeout=_http_timeout()) as client:
        response = client.get(f"{_api_base()}/debts/{debt_id}")
        response.raise_for_status()
        return response.json()


def create_debt(payload: dict) -> dict:
    with httpx.Client(timeout=_http_timeout()) as client:
        response = client.post(f"{_api_base()}/debts", json=payload)
        response.raise_for_status()
        return response.json()


def update_debt(debt_id: int, payload: dict) -> dict:
    with httpx.Client(timeout=_http_timeout()) as client:
        response = client.put(f"{_api_base()}/debts/{debt_id}", json=payload)
        response.raise_for_status()
        return response.json()


def delete_debt(debt_id: int) -> None:
    """ลบหลายทางตามลำดับ: JSON body → path POST → DELETE (พร็อกซี/เวอร์ชัน API ต่างกัน)."""
    base = _api_base().rstrip("/")
    with httpx.Client(timeout=_http_timeout(), follow_redirects=True) as client:
        r = client.post(f"{base}/debts/remove", json={"debt_id": debt_id})
        if r.status_code not in (404, 405):
            r.raise_for_status()
            return
        r = client.post(f"{base}/debts/{debt_id}/delete")
        if r.status_code not in (404, 405):
            r.raise_for_status()
            return
        r = client.delete(f"{base}/debts/{debt_id}")
        r.raise_for_status()


def list_installments(debt_id: int) -> list[dict]:
    with httpx.Client(timeout=_http_timeout()) as client:
        response = client.get(f"{_api_base()}/debts/{debt_id}/installments")
        response.raise_for_status()
        return response.json()
