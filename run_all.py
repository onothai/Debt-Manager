from __future__ import annotations

import subprocess
import sys
import time
from urllib.request import urlopen
from urllib.error import URLError


API_URL = "http://127.0.0.1:8000/health"


def api_is_up() -> bool:
    try:
        with urlopen(API_URL, timeout=1.5) as resp:
            return resp.status == 200
    except URLError:
        return False


def main() -> None:
    api_process: subprocess.Popen[str] | None = None
    started_here = False

    try:
        if not api_is_up():
            print("Starting FastAPI server on port 8000 ...")
            api_process = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"],
            )
            started_here = True

            for _ in range(20):
                if api_is_up():
                    break
                time.sleep(0.4)

        if not api_is_up():
            raise RuntimeError("API did not start. Please check database/API logs.")

        print("Starting Flet app ...")
        subprocess.run([sys.executable, "flet_app.py"], check=True)
    finally:
        if started_here and api_process is not None:
            api_process.terminate()
            try:
                api_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                api_process.kill()


if __name__ == "__main__":
    main()
