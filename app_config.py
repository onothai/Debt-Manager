"""โหลด .env และคำนวณ URL ของ FastAPI ให้ตรงกับ uvicorn (host/port).

ลำดับความสำคัญ:
  1) API_BASE_URL (เต็ม string)
  2) UVICORN_HOST + UVICORN_PORT
  3) DB_HOST (จาก .env เดียวกับ api.py — กรณีอัปโหลดแค่ DB ไม่ได้ใส่ UVICORN_*)
  4) ค่าเริ่มต้น lab: host ตรง api.py, port 3500 (ตรง uvicorn ที่โปรเจกต์นี้ใช้บ่อย)

ถ้า API อยู่พอร์ต 8000: ใส่ใน .env ว่า UVICORN_PORT=8000
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

_ROOT = Path(__file__).resolve().parent
load_dotenv(_ROOT / ".env")

# ตรงกับค่าเริ่มต้น DB_HOST ใน api.py — กรณีไม่มีไฟล์ .env เลย ยังชี้เครื่อง lab ได้
_DEFAULT_HOST = "192.168.137.50"
_DEFAULT_API_PORT = "3500"


def client_api_base_url() -> str:
    """URL ที่ client (Flet / httpx) ใช้เรียก API — ต้องตรงกับที่รัน uvicorn."""
    explicit = os.getenv("API_BASE_URL", "").strip()
    if explicit:
        return explicit.rstrip("/")
    host = (
        os.getenv("UVICORN_HOST") or os.getenv("DB_HOST") or _DEFAULT_HOST
    ).strip() or _DEFAULT_HOST
    port = (os.getenv("UVICORN_PORT") or _DEFAULT_API_PORT).strip() or _DEFAULT_API_PORT
    if host in ("0.0.0.0", "::"):
        host = "127.0.0.1"
    return f"http://{host}:{port}"
