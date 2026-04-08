"""
รัน FastAPI (:8000) แล้วรัน Flet แบบเว็บ (:3500 ตามค่าเริ่มต้นใน run_flet_web.py)

ก่อนรัน: ตั้งค่า DB_* / DB_USER ฯลฯ ตาม api.py
PowerShell:
  $env:DB_USER = 'api_user'
  $env:DB_PASSWORD = '...'
  python run_all_web.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen


API_HEALTH = "http://127.0.0.1:8000/health"


def api_is_up() -> bool:
    try:
        with urlopen(API_HEALTH, timeout=1.5) as resp:
            return resp.status == 200
    except URLError:
        return False


def main() -> None:
    api_process: subprocess.Popen[str] | None = None
    started_here = False

    try:
        if not api_is_up():
            print("Starting FastAPI on :8000 ...")
            api_process = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"],
            )
            started_here = True
            for _ in range(25):
                if api_is_up():
                    break
                time.sleep(0.4)

        if not api_is_up():
            raise RuntimeError("API ไม่ขึ้นที่ http://127.0.0.1:8000 — ตรวจ DB และ log uvicorn")

        # แอปเว็บบนเครื่องเดียวกัน → ชี้ API ที่ localhost (ยกเว้นตั้ง API_BASE_URL ไว้แล้ว)
        env = os.environ.copy()
        env.setdefault("API_BASE_URL", "http://127.0.0.1:8000")
        env.setdefault("FLET_WEB_PORT", "3500")
        print("Starting Flet web (ค่าเริ่มต้นพอร์ต 3500 — ดู URL ที่ run_flet_web พิมพ์ต่อ) ...")
        subprocess.run([sys.executable, "run_flet_web.py"], check=True, env=env)
    finally:
        if started_here and api_process is not None:
            api_process.terminate()
            try:
                api_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                api_process.kill()


if __name__ == "__main__":
    main()
