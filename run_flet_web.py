"""
รันแอป Debt Manager ผ่านเบราว์เซอร์ (Flet web server).

ชื่อไฟล์ต้องไม่ใช่ flet_web.py — จะไปบดบังแพ็กเกจ flet_web จาก PyPI

รันจากโฟลเดอร์โปรเจกต์ (ที่มี flet_app.py):
  cd D:\\Dowloard_D\\kimp
  python run_flet_web.py

เงื่อนไขที่รองรับ:
  • เว็บ Flet บนคอม: bind 0.0.0.0 พอร์ตเริ่มต้น 3500 → เปิด http://<IP-คอม>:3500
  • มือถือ: ต่อ WiFi วงเดียวกับคอม แล้วเปิดเลข IP เดียวกับคอม (ไม่ใช่ 127.0.0.1)
  • แอปหน้าต่าง: python flet_app.py

API ต้องรันบนเครื่องเดียวกับ run_flet_web (httpx ฝั่ง Python) — URL จาก .env / app_config
PowerShell:
  $env:FLET_WEB_PORT = '3550'   # คนละพอร์ตกับ uvicorn
  $env:FLET_SERVER_IP = '0.0.0.0'
  $env:FLET_WEB_RENDERER = 'canvaskit'   # ค่าเริ่มต้น — GIF พื้นหลังบนมือถือ (auto มักทำให้ภาพนิ่ง)
  $env:FLET_WEB_RENDERER = 'auto'        # โหลดครั้งแรกเบากว่า แต่พื้นหลังอาจไม่ขยับบนมือถือ
  $env:FLET_DISABLE_BG_GIF_WEB = '1'   # ถ้า WebSocket หนัก / ค้าง
  python run_flet_web.py
"""
from __future__ import annotations

import logging
import os
import socket

import flet as ft

import app_config
from flet_app import ASSETS_DIR, main


# uvicorn จะ log ERROR ทุกครั้งที่เบราว์เซอร์ตัด WebSocket (รีเฟรช/ปิดแท็บ) — ไม่ใช่บั๊กแอป
_WS_DISCONNECT_NAMES = frozenset({"WebSocketDisconnect", "ClientDisconnected"})


class _IgnoreExpectedWebSocketDisconnect(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if record.exc_info and record.exc_info[0] is not None:
            if record.exc_info[0].__name__ in _WS_DISCONNECT_NAMES:
                return False
        return True


def _quiet_expected_websocket_errors() -> None:
    """กด log ERROR จากการตัด WebSocket แบบปกติ (ยกเว้นตั้ง FLET_SHOW_WS_ERRORS=1)."""
    if os.environ.get("FLET_SHOW_WS_ERRORS", "").strip().lower() in ("1", "true", "yes", "on"):
        return
    flt = _IgnoreExpectedWebSocketDisconnect()
    for _name in ("uvicorn.error", "uvicorn"):
        logging.getLogger(_name).addFilter(flt)


def _guess_lan_ipv4() -> str | None:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return None


def _patch_flet_open_browser_url_when_bind_all_interfaces() -> None:
    """Flet ตั้ง url_host = host เมื่อ bind 0.0.0.0 เลยเด้งเบราว์เซอร์ไป http://0.0.0.0:port/ — ใช้ไม่ได้จริง.

    ยัง bind 0.0.0.0 ตามเดิม แต่ให้ URL ที่เปิดอัตโนมัติเป็น http://127.0.0.1:port/
    """
    import flet_web.fastapi.serve_fastapi_web_app as sfw

    _orig = sfw.serve_fastapi_web_app

    async def _wrapped(main, **kwargs):  # type: ignore[no-untyped-def]
        if kwargs.get("host") == "0.0.0.0" and kwargs.get("url_host") == "0.0.0.0":
            kwargs = {**kwargs, "url_host": "127.0.0.1"}
        return await _orig(main, **kwargs)

    sfw.serve_fastapi_web_app = _wrapped


if __name__ == "__main__":
    try:
        import PIL  # noqa: F401
    except ImportError:
        print(
            "[run_flet_web] ไม่มี Pillow — GIF พื้นหลังจะไม่สลับเฟรมบนเว็บ\n"
            "  แก้:  .\\env\\Scripts\\pip install Pillow\n"
            "  แล้วรัน:  .\\env\\Scripts\\python.exe run_flet_web.py"
        )
    host = os.environ.get("FLET_SERVER_IP", "0.0.0.0")
    port = int(os.environ.get("FLET_WEB_PORT", "3500"))
    lan = _guess_lan_ipv4()
    print(f"Flet web ฟังที่ {host}:{port}  (0.0.0.0 = เปิดรับทุก interface — อย่าพิมพ์ URL เป็น http://0.0.0.0 ในเบราว์เซอร์)")
    print(f"  เปิดบนเครื่องเดียวกับที่รัน: http://127.0.0.1:{port}  หรือ  http://localhost:{port}")
    if lan and host in ("0.0.0.0", ""):
        print(f"  มือถือ (WiFi เดียวกัน): http://{lan}:{port}")
        print("  ถ้าเปิดไม่ได้ ตรวจ Windows Firewall ให้อนุญาตพอร์ตนี้ (Inbound)")
    print(
        "  FastAPI ต้องรันที่เครื่องนี้ด้วย (มือถือเรียก API ผ่านเซิร์ฟเวอร์ Python ไม่ใช่จากเครื่องมือถือ):"
    )
    _api = app_config.client_api_base_url()
    print(f"    แอปจะเรียก API ที่ {_api} (จาก .env: API_BASE_URL หรือ UVICORN_HOST+UVICORN_PORT)")
    print("    ตัวอย่าง: uvicorn api:app --host 192.168.137.50 --port 3500")
    print(f"    ตรวจ API: {_api}/health  (Swagger /docs อยู่ที่พอร์ตของ API ไม่ใช่พอร์ต Flet เว็บ)")
    print(
        "  log WebSocket หลังปิดแท็บ/รีเฟรช = ปกติ (โปรแกรมจะกรอง ERROR นี้ให้); "
        "อยากเห็นเต็ม: $env:FLET_SHOW_WS_ERRORS='1'"
    )
    print(
        "  ค่าเริ่มต้นใช้ canvaskit เพื่อให้ GIF พื้นหลังขยับบนมือถือได้; ถ้าโหลดช้า: $env:FLET_WEB_RENDERER='auto'"
    )
    _quiet_expected_websocket_errors()
    _patch_flet_open_browser_url_when_bind_all_interfaces()

    # canvaskit = วาดสม่ำเสมอทุกเครื่อง — auto บนมือถือมักเป็น renderer ที่อัปเดตรูปพื้นหลังไม่ได้ → GIF นิ่ง
    _wr = (os.environ.get("FLET_WEB_RENDERER") or "canvaskit").strip().lower()
    web_renderer = (
        ft.WebRenderer.AUTO
        if _wr in ("auto", "")
        else ft.WebRenderer.SKWASM
        if _wr == "skwasm"
        else ft.WebRenderer.CANVAS_KIT
    )
    ft.run(
        main,
        assets_dir=ASSETS_DIR,
        view=ft.AppView.WEB_BROWSER,
        host=host,
        port=port,
        web_renderer=web_renderer,
    )
