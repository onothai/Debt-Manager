from __future__ import annotations

import asyncio
import base64
import io
import math
import os
from concurrent.futures import Future as ConcurrentFuture
from urllib.parse import urljoin, urlparse

import app_config  # noqa: F401 — โหลด .env; URL API ใช้ client_api_base_url()
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

import flet as ft
import httpx

from ui.layout import layout_content_width, layout_mobile_breakpoint, page_content_padding
from ui.api_client import (
    create_debt,
    create_user,
    delete_debt,
    get_debt,
    get_user,
    get_users,
    list_debts,
    update_debt,
    update_user_debt_total,
)
from ui.loan_math import compute_installment_schedule_api_style, compute_reducing_balance_schedule
from ui.theme import (
    APP_THEME,
    BG_DARK,
    GREEN_DARK,
    TEXT_LIGHT,
    TEXT_SOFT,
    format_integer_typing_display,
    format_money_decimal_display,
    format_money_typing_display,
    strip_money_input,
)
from ui.views.dashboard_view import build_dashboard_view
from ui.views.debt_form_view import build_debt_form_view
from ui.views.debts_list_view import build_debts_list_view
from ui.views.login_view import build_login_view
from ui.views.result_view import build_result_view
from ui.views.signup_view import build_signup_view
from ui.date_picker_field import attach_date_picker


ASSETS_DIR = os.path.join(os.path.dirname(__file__), "img")
# ไฟล์ GIF ใหญ่มากจะทำให้เว็บบนมือถือโหลดช้า/ค้าง; Flutter web บางทีแสดงแค่เฟรมแรก (ดูไม่ขยับ)
BACKGROUND_GIF_CANDIDATES = ["m6.gif", "money.gif", "source.gif"]

# พลิกการ์ดแนวหนังสือ (หมุนรอบแกน Y) — ใช้ Matrix4 + perspective
# ลด STEP_SEC / STEPS ให้เร็วขึ้น; เพิ่ม STEPS ถ้าอยากลื่นขึ้น (แล้วอาจลด STEP_SEC เล็กน้อย)
_AUTH_FLIP_STEPS = 12
_AUTH_FLIP_STEP_SEC = 0.01
_AUTH_PERSPECTIVE = 0.0012


def _auth_transform_rotate_y(angle_rad: float) -> ft.Transform:
    m = ft.Matrix4.identity()
    m.set_entry(3, 2, _AUTH_PERSPECTIVE)
    m.rotate_y(angle_rad)
    return ft.Transform(matrix=m, alignment=ft.Alignment.CENTER)


def _to_decimal(value: str) -> Decimal:
    return Decimal(value.strip())


def _norm_freq_key(raw: object, *, default: str = "month") -> str:
    """แปลงค่าจาก Dropdown/SegmentedButton/DB เป็น week|month|year (รองรับข้อความไทย)."""
    s = str(raw or "").strip().lower()
    t = str(raw or "").strip()
    if s in ("week", "month", "year"):
        return s
    if "สัปดาห์" in t or "week" in s:
        return "week"
    if "เดือน" in t or "month" in s:
        return "month"
    if "ปี" in t or "year" in s:
        return "year"
    if default in ("week", "month", "year"):
        return default
    return "month"


def _api_failure_message(exc: BaseException) -> str:
    api_base = app_config.client_api_base_url()
    if isinstance(exc, httpx.TimeoutException):
        return (
            f"หมดเวลารอ API ({api_base}) — บนเครื่องรันแอป เปิดเบราว์เซอร์ไป {api_base}/health "
            f"ถ้าไม่ขึ้น ให้รัน uvicorn ให้ตรงกับ .env (UVICORN_HOST / UVICORN_PORT); "
            "ถ้า DB ช้า ลองใน PowerShell: $env:API_HTTP_TIMEOUT='180'"
        )
    if isinstance(exc, httpx.ConnectError):
        if "127.0.0.1" in api_base or "localhost" in api_base.lower():
            return (
                f"ต่อ API ไม่ได้ ({api_base}) — รัน FastAPI ให้ตรงกับ {api_base} "
                "(ตรวจ .env: UVICORN_HOST / UVICORN_PORT หรือ API_BASE_URL; "
                "โหมดเว็บ: httpx ทำงานที่เครื่องรัน Python — 127.0.0.1 = เครื่องนั้น)"
            )
        return (
            f"ต่อ API ไม่ได้ ({api_base}) — เปิด uvicorn + firewall พอร์ตที่ใช้; "
            "หรือแก้ .env ให้ API_BASE_URL / UVICORN_* ตรงกับ URL ที่เปิด Swagger (/docs) ตอนลบสำเร็จ"
        )
    if isinstance(exc, httpx.HTTPStatusError):
        resp = exc.response
        detail = ""
        try:
            body = resp.json()
            if isinstance(body, dict) and "detail" in body:
                d = body["detail"]
                detail = "; ".join(str(x) for x in d) if isinstance(d, list) else str(d)
            elif body:
                detail = str(body)[:300]
        except Exception:
            detail = (resp.text or "")[:300]
        if not detail:
            detail = resp.reason_phrase or str(resp.status_code)
        req_url = ""
        try:
            if resp.request is not None:
                req_url = str(resp.request.url)
        except Exception:
            pass
        hint = (
            f" แอปอ่านฐาน API จาก .env = {api_base}"
            + (f" | URL ที่เรียกล่าสุด: {req_url}" if req_url else "")
            + " — ต้องตรงกับที่เปิด Swagger (/docs) ตอนลบสำเร็จ"
        )
        return f"API ตอบ {resp.status_code}: {detail}.{hint}"
    return f"เชื่อมต่อ API ไม่สำเร็จ: {exc}"


def _background_src() -> str:
    # Use plain asset name (no leading "/") for better compatibility
    # across Flet desktop/web builds.
    for name in BACKGROUND_GIF_CANDIDATES:
        if os.path.exists(os.path.join(ASSETS_DIR, name)):
            return name
    return ""


def _env_truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes", "on")


def _use_background_gif(page: ft.Page) -> bool:
    # GIF ใหญ่ + render ถี่บนเว็บ มักทำให้ log WebSocket ClientDisconnected (ไม่เป็นอันตรายถ้าแอปยังใช้ได้)
    if _env_truthy("FLET_DISABLE_BG_GIF"):
        return False
    if getattr(page, "web", False) and _env_truthy("FLET_DISABLE_BG_GIF_WEB"):
        return False
    return True


def _is_mobile_web(page: ft.Page) -> bool:
    """เบราว์เซอร์บนมือถือ (Flet web) — GIF พื้นหลังมักแสดงนิ่งถ้าใช้ HTML renderer."""
    if not getattr(page, "web", False):
        return False
    plat = getattr(page, "platform", None)
    if plat in ("ios", "android"):
        return True
    ua = (getattr(page, "client_user_agent", None) or "").lower()
    return any(
        x in ua
        for x in (
            "mobile",
            "iphone",
            "ipad",
            "ipod",
            "android",
            "webos",
            "samsungbrowser",
            "samsung",
        )
    )


def _use_manual_gif_frames(page: ft.Page) -> bool:
    """บนเว็บ: สลับเฟรม GIF ด้วย Pillow (ค่าเริ่มต้นเปิดทุกเว็บ).

    Chrome มือถือในโหมดมือถือมักไม่เล่น GIF แอนิเมชัน; พอขอ 'เว็บไซต์สำหรับเดสก์ท็อป'
    จะได้ viewport/UA แบบเดสก์ท็อปแล้ว GIF ขยับ — จึงให้โหมดสลับเฟรมทำงานเสมอบน web
    ไม่ต้องพึ่งปุ่มนั้น (ยกเว้นตั้ง FLET_BG_GIF_WEB_NATIVE=1)
    """
    if not getattr(page, "web", False):
        return False
    if _env_truthy("FLET_DISABLE_MANUAL_GIF_ANIM"):
        return False
    if _env_truthy("FLET_BG_GIF_WEB_NATIVE"):
        return False
    return True


def _gif_load_failure_reason(asset_path: str) -> str:
    """ข้อความอธิบายเมื่อ _load_gif_animation_frames คืน None (สำหรับ log)."""
    if not os.path.isfile(asset_path):
        return f"ไม่พบไฟล์ {asset_path!r}"
    try:
        from PIL import Image
    except ImportError:
        return (
            "ไม่มี Pillow ใน Python ที่รัน Flet — รัน: .\\env\\Scripts\\pip install Pillow "
            "แล้วใช้ .\\env\\Scripts\\python.exe run_flet_web.py (อย่าใช้ Python ระบบที่ยังไม่มี Pillow)"
        )
    im = None
    try:
        im = Image.open(asset_path)
        n = int(getattr(im, "n_frames", 1) or 1)
        anim = bool(getattr(im, "is_animated", False))
        if n < 2 and not anim:
            return "GIF มีแค่ 1 เฟรม (ไม่ใช่แอนิเมชัน)"
        return "แยกเฟรมไม่สำเร็จ (ไฟล์เสียหรือรูปแบบไม่รองรับ)"
    except Exception as ex:
        return f"อ่าน GIF ไม่ได้: {ex}"
    finally:
        if im is not None:
            try:
                im.close()
            except Exception:
                pass


def _load_gif_animation_frames(
    asset_path: str,
    *,
    max_frames: int = 48,
    max_side: int = 480,
    lite_web: bool = False,
) -> tuple[list[str], list[int]] | None:
    """แยกเฟรม GIF เป็น data URL สำหรับสลับบน Flet เว็บ (GIF แบบ native มักไม่ขยับ).

    lite_web: ย่อเฟรม + JPEG — ใช้กับทุกเบราว์เซอร์บนเว็บ (ไม่พึ่งจับ UA มือถือ)
    """
    try:
        from PIL import Image, ImageSequence
    except ImportError:
        return None
    if not os.path.isfile(asset_path):
        return None
    try:
        im = Image.open(asset_path)
    except Exception:
        return None
    n_frames = getattr(im, "n_frames", 1)
    if n_frames < 2 and not getattr(im, "is_animated", False):
        return None
    try:
        resample = Image.Resampling.LANCZOS
    except AttributeError:
        resample = Image.LANCZOS
    cap_frames = min(max_frames, 24) if lite_web else max_frames
    cap_side = min(max_side, 260) if lite_web else max_side
    # พื้นหลังใกล้ BG_DARK (#0A0E0A) ตอนแปลง RGBA → JPEG
    _jpeg_bg = (10, 14, 10)
    frames: list[str] = []
    delays: list[int] = []
    for i, frame in enumerate(ImageSequence.Iterator(im)):
        if i >= cap_frames:
            break
        rgba = frame.convert("RGBA")
        rgba.thumbnail((cap_side, cap_side), resample)
        buf = io.BytesIO()
        if lite_web:
            rgb = Image.new("RGB", rgba.size, _jpeg_bg)
            rgb.paste(rgba, mask=rgba.split()[3])
            rgb.save(buf, format="JPEG", quality=72, optimize=True)
            b64 = base64.b64encode(buf.getvalue()).decode("ascii")
            frames.append(f"data:image/jpeg;base64,{b64}")
        else:
            rgba.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode("ascii")
            frames.append(f"data:image/png;base64,{b64}")
        delays.append(int(frame.info.get("duration", 100) or 100))
    im.close()
    if not frames:
        return None
    return frames, delays


def _same_origin_gif_url(page: ft.Page, filename: str) -> str | None:
    """สร้าง http(s)://host:port/... ให้ตรงไฟล์ static — บางเคส GIF ขยับได้ดีกว่าใช้ชื่อ asset ล้วน."""
    if not filename or _env_truthy("FLET_BG_GIF_ASSET_ONLY"):
        return None
    base = getattr(page, "url", None) or ""
    if not base or not urlparse(base).scheme:
        return None
    base_norm = base if base.endswith("/") else base + "/"
    # โฟลเดอร์ assets_dir (img/) มักถูกเสิร์ฟที่ root ของ static → /m1.gif
    if _env_truthy("FLET_BG_GIF_USE_ASSETS_PREFIX"):
        return urljoin(base_norm, f"assets/{filename}")
    return urljoin(base_norm, filename)


def _build_background_image(page: ft.Page, bg_filename: str, vp_w: float, vp_h: float) -> ft.Control:
    """พื้นหลัง GIF — บนเว็บจอแคบลอง same-origin URL + fallback เป็น asset."""
    web = getattr(page, "web", False)
    narrow = web and (float(page.width or 0) <= 900 or float(page.width or 0) == 0)
    mobile_ua = web and _is_mobile_web(page)
    common = {
        "width": vp_w,
        "height": vp_h,
        "fit": "cover",
        "gapless_playback": False if (narrow or mobile_ua) else True,
        "filter_quality": ft.FilterQuality.MEDIUM if (narrow or mobile_ua) else ft.FilterQuality.LOW,
    }
    fallback = ft.Image(src=bg_filename, **common)
    if mobile_ua:
        url = _same_origin_gif_url(page, bg_filename)
        if url:
            return ft.Image(src=url, error_content=fallback, **common)
    return fallback


def main(page: ft.Page) -> None:
    api_base = app_config.client_api_base_url()
    print(f"[Debt Manager] ใช้ API ที่ {api_base} (แก้ใน .env: API_BASE_URL หรือ UVICORN_HOST/PORT)")

    page.title = "Debt Manager"
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = APP_THEME
    page.bgcolor = BG_DARK
    page.padding = 0
    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
    page.vertical_alignment = ft.MainAxisAlignment.START
    try:
        page.window.maximized = True
    except Exception:
        pass

    state = {
        "screen": "login",
        "username": "",
        "user_id": None,
        "status_message": "",
        "status_is_error": False,
        "debt_total": "",
        "debt_total_editing": False,
        "debt_total_backup": "",
        "interest_rate": "",
        "interest_term": "month",
        "_dash_pay_period": "month",
        "_api_pay_period": "month",
        "schedule_result": None,
        "debts_cache": [],
        "debts_list_error": "",
        "editing_debt_id": None,
        "debt_form_error": "",
        "debt_form_is_error": False,
        "bg_gif_frames": None,
        "bg_gif_delays": None,
        "bg_gif_frame_idx": 0,
        "bg_anim_img": None,
        "bg_anim_running": False,
        "_bg_gif_future": None,
        "_session_alive": True,
        "auth_book_flipping": False,
        "auth_flip_seq": 0,
        "_debt_formatting": False,
        "_api_principal_formatting": False,
        "_api_rate_formatting": False,
        "_api_installments_formatting": False,
    }

    controls = {
        "login_username": ft.TextField(label="Username"),
        "login_password": ft.TextField(label="Password", password=True, can_reveal_password=True),
        "signup_username": ft.TextField(label="Username"),
        "signup_password": ft.TextField(label="Password", password=True, can_reveal_password=True),
        "debt_total": ft.TextField(label="ยอดหนี้ (Debt Total)", hint_text="เช่น 50000"),
        "interest_rate": ft.TextField(label="ดอกเบี้ย (%)", value="7.5"),
        "interest_term": ft.Dropdown(
            label="",
            value="month",
            options=[
                ft.dropdown.Option(key="week", text="ทุกสัปดาห์"),
                ft.dropdown.Option(key="month", text="ทุกเดือน"),
                ft.dropdown.Option(key="year", text="ทุกปี"),
            ],
        ),
        "installment_count": ft.TextField(label="จำนวนงวด", hint_text="เช่น 12", value="12"),
        "first_due_date": ft.TextField(label="วันครบกำหนดงวดแรก", value=date.today().isoformat()),
        "api_debt_name": ft.TextField(label="ชื่อรายการหนี้", hint_text="เช่น รถ / บ้าน"),
        "api_debt_principal": ft.TextField(label="เงินต้น (บาท)", hint_text="เช่น 500000"),
        "api_debt_interest_rate": ft.TextField(label="อัตรา %", hint_text="เช่น 7.5"),
        "api_debt_interest_rate_basis": ft.Dropdown(
            label="",
            value="year",
            options=[
                ft.dropdown.Option(key="week", text="ต่อสัปดาห์"),
                ft.dropdown.Option(key="month", text="ต่อเดือน"),
                ft.dropdown.Option(key="year", text="ต่อปี"),
            ],
        ),
        "api_debt_interest_type": ft.Dropdown(
            label="รูปแบบดอกเบี้ย",
            value="reducing",
            options=[
                ft.dropdown.Option(key="flat", text="ดอกจากยอดกู้เต็ม"),
                ft.dropdown.Option(key="reducing", text="ดอกจากยอดที่เหลือ"),
            ],
        ),
        "api_debt_payment_period": ft.Dropdown(
            label="",
            value="month",
            options=[
                ft.dropdown.Option(key="week", text="ทุกสัปดาห์"),
                ft.dropdown.Option(key="month", text="ทุกเดือน"),
                ft.dropdown.Option(key="year", text="ทุกปี"),
            ],
        ),
        "api_debt_installments": ft.TextField(label="จำนวนงวด", hint_text="เช่น 60"),
        "api_debt_start_date": ft.TextField(
            label="วันเริ่มงวดแรก (ประมาณ)",
            hint_text="แตะเพื่อเลือกจากปฏิทิน",
            value=date.today().isoformat(),
        ),
    }

    def _effective_pay_period(dd: ft.Dropdown, state_key: str, default: str) -> str:
        """อ่านความถี่ผ่อนจาก Dropdown + state (รองรับค่า key หรือข้อความไทยหลัง render บนเว็บ)."""
        prev = state.get(state_key, default)
        k = _norm_freq_key(dd.value, default=prev)
        state[state_key] = k
        return k

    def set_status(message: str, is_error: bool = False) -> None:
        state["status_message"] = message
        state["status_is_error"] = is_error

    def set_debt_form_status(message: str, is_error: bool = False) -> None:
        state["debt_form_error"] = message
        state["debt_form_is_error"] = is_error

    def refresh_debts_list() -> None:
        uid = state.get("user_id")
        if uid is None:
            state["debts_cache"] = []
            state["debts_list_error"] = ""
            return
        try:
            state["debts_cache"] = list_debts(int(uid))
            state["debts_list_error"] = ""
        except Exception as ex:
            state["debts_cache"] = []
            state["debts_list_error"] = _api_failure_message(ex)

    def _sync_debt_from_api() -> None:
        uid = state.get("user_id")
        if uid is None:
            controls["debt_total"].value = "0"
            return
        try:
            u = get_user(int(uid))
            controls["debt_total"].value = format_money_decimal_display(u.get("debt_total"))
        except Exception:
            controls["debt_total"].value = "0"

    def go(screen: str) -> None:
        if screen not in ("login", "signup"):
            controls.pop("auth_flip_wrap", None)
            state["auth_flip_seq"] = state.get("auth_flip_seq", 0) + 1
            state["auth_book_flipping"] = False
        if screen != "dashboard":
            state["debt_total_editing"] = False
        state["screen"] = screen
        if screen == "dashboard":
            state["schedule_result"] = None
            _sync_debt_from_api()
        elif screen == "debts_list":
            refresh_debts_list()
        render()

    def on_edit_debt(_: ft.ControlEvent) -> None:
        state["debt_total_backup"] = (controls["debt_total"].value or "").strip() or "0"
        state["debt_total_editing"] = True
        render()

    def on_debt_total_change(_: ft.ControlEvent) -> None:
        if state.get("_debt_formatting"):
            return
        if not state.get("debt_total_editing"):
            return
        state["_debt_formatting"] = True
        try:
            cur = controls["debt_total"].value or ""
            new_val = format_money_typing_display(cur)
            if new_val != cur:
                controls["debt_total"].value = new_val
                page.update()
        finally:
            state["_debt_formatting"] = False

    def on_api_debt_principal_change(_: ft.ControlEvent) -> None:
        if state.get("_api_principal_formatting"):
            return
        state["_api_principal_formatting"] = True
        try:
            cur = controls["api_debt_principal"].value or ""
            new_val = format_money_typing_display(cur)
            if new_val != cur:
                controls["api_debt_principal"].value = new_val
                page.update()
        finally:
            state["_api_principal_formatting"] = False

    def on_api_debt_interest_rate_change(_: ft.ControlEvent) -> None:
        if state.get("_api_rate_formatting"):
            return
        state["_api_rate_formatting"] = True
        try:
            cur = controls["api_debt_interest_rate"].value or ""
            new_val = format_money_typing_display(cur)
            if new_val != cur:
                controls["api_debt_interest_rate"].value = new_val
                page.update()
        finally:
            state["_api_rate_formatting"] = False

    def on_api_debt_installments_change(_: ft.ControlEvent) -> None:
        if state.get("_api_installments_formatting"):
            return
        state["_api_installments_formatting"] = True
        try:
            cur = controls["api_debt_installments"].value or ""
            new_val = format_integer_typing_display(cur)
            if new_val != cur:
                controls["api_debt_installments"].value = new_val
                page.update()
        finally:
            state["_api_installments_formatting"] = False

    def on_cancel_debt(_: ft.ControlEvent) -> None:
        controls["debt_total"].value = state.get("debt_total_backup", "0")
        state["debt_total_editing"] = False
        render()

    def on_save_debt(_: ft.ControlEvent) -> None:
        try:
            debt_total = _to_decimal(strip_money_input(controls["debt_total"].value or "0"))
        except (InvalidOperation, ValueError):
            set_status("กรุณากรอกตัวเลขให้ถูกต้อง", True)
            render()
            return
        if debt_total < 0:
            set_status("กรุณากรอกค่าที่มากกว่า 0", True)
            render()
            return
        uid = state.get("user_id")
        if uid is None:
            state["debt_total_editing"] = False
            set_status("")
            render()
            return
        try:
            update_user_debt_total(int(uid), float(debt_total))
            state["debt_total_editing"] = False
            set_status("")
            _sync_debt_from_api()
            render()
        except Exception as ex:
            set_status(_api_failure_message(ex), True)
            render()

    def do_login(_: ft.ControlEvent) -> None:
        username = (controls["login_username"].value or "").strip()
        password = (controls["login_password"].value or "").strip()
        if not username or not password:
            set_status("กรุณากรอก username และ password", True)
            render()
            return
        try:
            users = get_users()
            found = next((u for u in users if u.get("username") == username and u.get("password") == password), None)
            if not found:
                set_status("เข้าสู่ระบบไม่สำเร็จ", True)
                render()
                return
            state["username"] = username
            state["user_id"] = found.get("user_id")
            set_status("")
            go("dashboard")
        except Exception as ex:
            set_status(_api_failure_message(ex), True)
            render()

    def do_signup(_: ft.ControlEvent) -> None:
        username = (controls["signup_username"].value or "").strip()
        password = (controls["signup_password"].value or "").strip()
        if not username or not password:
            set_status("กรุณากรอก username และ password สำหรับสมัครสมาชิก", True)
            render()
            return
        try:
            created_user = create_user(username, password)
            state["username"] = username
            state["user_id"] = created_user.get("user_id")
            set_status("")
            go("dashboard")
        except Exception as ex:
            set_status(_api_failure_message(ex), True)
            render()

    def build_auth_body(screen_name: str, content_width: float) -> ft.Control:
        """เนื้อหา Login / Signup (ไม่รวม wrapper พลิกการ์ด)"""
        if screen_name == "login":
            return build_login_view(
                content_width=content_width,
                username_field=controls["login_username"],
                password_field=controls["login_password"],
                status_message=state["status_message"],
                status_is_error=state["status_is_error"],
                on_login=do_login,
                on_go_signup=lambda _: switch_auth("signup"),
            )
        return build_signup_view(
            content_width=content_width,
            username_field=controls["signup_username"],
            password_field=controls["signup_password"],
            status_message=state["status_message"],
            status_is_error=state["status_is_error"],
            on_signup=do_signup,
            on_go_login=lambda _: switch_auth("login"),
        )

    async def _flip_auth_book(target_screen: str, seq: int) -> None:
        """พลิกแนวหนังสือ: 0→π/2 แล้วสลับเนื้อหา แล้ว -π/2→0"""
        half_pi = math.pi / 2
        try:
            cw = layout_content_width(float(page.width or 390))
            for s in range(1, _AUTH_FLIP_STEPS + 1):
                if state.get("auth_flip_seq") != seq:
                    return
                wrap = controls.get("auth_flip_wrap")
                if wrap is None:
                    return
                wrap.transform = _auth_transform_rotate_y(half_pi * (s / _AUTH_FLIP_STEPS))
                page.update()
                await asyncio.sleep(_AUTH_FLIP_STEP_SEC)
            if state.get("auth_flip_seq") != seq:
                return
            wrap = controls.get("auth_flip_wrap")
            if wrap is None:
                return
            state["screen"] = target_screen
            wrap.content = build_auth_body(target_screen, cw)
            wrap.transform = _auth_transform_rotate_y(-half_pi)
            page.update()
            for s in range(1, _AUTH_FLIP_STEPS + 1):
                if state.get("auth_flip_seq") != seq:
                    return
                wrap = controls.get("auth_flip_wrap")
                if wrap is None:
                    return
                a = -half_pi + half_pi * (s / _AUTH_FLIP_STEPS)
                wrap.transform = _auth_transform_rotate_y(a)
                page.update()
                await asyncio.sleep(_AUTH_FLIP_STEP_SEC)
            if state.get("auth_flip_seq") != seq:
                return
            wrap = controls.get("auth_flip_wrap")
            if wrap is not None:
                wrap.transform = _auth_transform_rotate_y(0)
                page.update()
        finally:
            if state.get("auth_flip_seq") == seq:
                state["auth_book_flipping"] = False

    def switch_auth(target_screen: str) -> None:
        """สลับ Login ↔ Signup แบบพลิกหน้า (หมุนรอบแกน Y)."""
        if state["screen"] == target_screen:
            return
        if target_screen not in ("login", "signup") or state["screen"] not in ("login", "signup"):
            go(target_screen)
            return
        if state.get("auth_book_flipping"):
            return
        wrap = controls.get("auth_flip_wrap")
        if wrap is None:
            state["screen"] = target_screen
            render()
            return
        state["auth_book_flipping"] = True
        state["auth_flip_seq"] = state.get("auth_flip_seq", 0) + 1
        seq = state["auth_flip_seq"]

        async def _runner() -> None:
            await _flip_auth_book(target_screen, seq)

        page.run_task(_runner)

    def go_result(_: ft.ControlEvent) -> None:
        try:
            debt_total = _to_decimal(strip_money_input(controls["debt_total"].value or "0"))
            interest_rate = _to_decimal(controls["interest_rate"].value or "0")
        except (InvalidOperation, ValueError):
            set_status("กรุณากรอกตัวเลขให้ถูกต้อง", True)
            render()
            return

        if debt_total <= 0:
            set_status("ยอดหนี้ต้องมากกว่า 0 เพื่อคำนวณตารางผ่อน", True)
            render()
            return
        if interest_rate < 0:
            set_status("อัตราดอกเบี้ยต้องไม่ติดลบ", True)
            render()
            return

        raw_n = strip_money_input(controls["installment_count"].value or "")
        try:
            n = int(raw_n) if raw_n else 0
        except ValueError:
            set_status("จำนวนงวดต้องเป็นจำนวนเต็ม", True)
            render()
            return
        if n < 1:
            set_status("กรุณากรอกจำนวนงวดอย่างน้อย 1", True)
            render()
            return

        due_raw = (controls["first_due_date"].value or "").strip()
        try:
            first_due = datetime.strptime(due_raw, "%Y-%m-%d").date()
        except ValueError:
            set_status("วันครบกำหนดงวดแรกต้องเป็นรูปแบบ YYYY-MM-DD", True)
            render()
            return

        pay_period = _effective_pay_period(controls["interest_term"], "_dash_pay_period", "month")
        try:
            rows, summary = compute_reducing_balance_schedule(
                debt_total,
                interest_rate,
                n,
                first_due,
                pay_period,
            )
        except ValueError as ve:
            set_status(str(ve), True)
            render()
            return

        state["result_back_screen"] = "dashboard"
        state["result_view_intro"] = None
        state["result_back_label"] = None
        state["result_interest_rate_basis"] = None
        state["debt_total"] = str(debt_total)
        state["interest_rate"] = str(interest_rate)
        state["interest_term"] = pay_period
        state["installment_count"] = str(n)
        state["first_due_date"] = first_due.isoformat()
        state["schedule_result"] = {"rows": rows, "summary": summary}

        if state["user_id"] is not None:
            try:
                update_user_debt_total(int(state["user_id"]), float(debt_total))
            except Exception as ex:
                set_status(_api_failure_message(ex), True)
                render()
                return

        set_status("")
        go("result")

    def _result_intro_for_saved_schedule(itype: str) -> str:
        if itype == "flat":
            return "สรุปผลการคำนวณ (ดอกจากยอดกู้เต็ม — เงินต้นต่องวดเท่ากัน · ตรงกับรูปแบบที่บันทึก)"
        return "สรุปผลการคำนวณ (ดอกจากยอดคงค้าง — เงินต้นต่องวดเท่ากัน · ตรงกับรูปแบบที่บันทึก)"

    def preview_debt_form_schedule(_: ft.ControlEvent) -> None:
        try:
            principal = _to_decimal(strip_money_input(controls["api_debt_principal"].value or "0"))
            rate = _to_decimal(controls["api_debt_interest_rate"].value or "0")
            n = int(strip_money_input(controls["api_debt_installments"].value or ""))
            start = datetime.strptime((controls["api_debt_start_date"].value or "").strip(), "%Y-%m-%d").date()
        except (InvalidOperation, ValueError):
            set_debt_form_status("กรุณากรอกเงินต้น ดอกเบี้ย จำนวนงวด และวันที่ให้ถูกต้อง", True)
            render()
            return
        if principal <= 0 or rate < 0 or n < 1:
            set_debt_form_status("เงินต้น ดอกเบี้ย และจำนวนงวดไม่ถูกต้อง", True)
            render()
            return
        itype = controls["api_debt_interest_type"].value or "reducing"
        rb = _norm_freq_key(controls["api_debt_interest_rate_basis"].value, default="year")
        if rb not in ("week", "month", "year"):
            rb = "year"
        pp = _effective_pay_period(controls["api_debt_payment_period"], "_api_pay_period", "month")
        try:
            rows, summary = compute_installment_schedule_api_style(
                principal,
                rate,
                n,
                start,
                rate_basis=rb,
                payment_period=pp,
                flat_interest=(itype == "flat"),
            )
        except ValueError as ve:
            set_debt_form_status(str(ve), True)
            render()
            return
        state["debt_total"] = str(principal)
        state["interest_rate"] = str(rate)
        state["interest_term"] = pp
        state["installment_count"] = str(n)
        state["first_due_date"] = rows[0]["due"].isoformat()
        state["schedule_result"] = {"rows": rows, "summary": summary}
        state["result_back_screen"] = "debt_form"
        state["result_view_intro"] = _result_intro_for_saved_schedule(itype)
        state["result_back_label"] = "กลับไปฟอร์มหนี้"
        state["result_interest_rate_basis"] = rb
        set_debt_form_status("", False)
        go("result")

    def preview_debt_from_list(debt_id: int) -> None:
        cache = state.get("debts_cache") or []
        d = next((x for x in cache if int(x["debt_id"]) == int(debt_id)), None)
        if d is None:
            state["debts_list_error"] = "ไม่พบรายการในรายการที่โหลด — ลองกลับแล้วเปิดหน้ารายการใหม่"
            render()
            return
        try:
            principal = Decimal(str(d["principal"]))
            rate = Decimal(str(d["interest_rate"]))
            n = int(d["total_installments"])
            sd = d.get("start_date")
            start = datetime.strptime(str(sd)[:10], "%Y-%m-%d").date()
        except (InvalidOperation, ValueError, TypeError, KeyError):
            state["debts_list_error"] = "ข้อมูลรายการหนี้ไม่ครบหรือไม่ถูกต้อง"
            render()
            return
        itype = str(d.get("interest_type", "reducing"))
        rb = _norm_freq_key(d.get("interest_rate_basis", "year"), default="year")
        if rb not in ("week", "month", "year"):
            rb = "year"
        pp = _norm_freq_key(d.get("payment_period", "month"), default="month")
        try:
            rows, summary = compute_installment_schedule_api_style(
                principal,
                rate,
                n,
                start,
                rate_basis=rb,
                payment_period=pp,
                flat_interest=(itype == "flat"),
            )
        except ValueError as ve:
            state["debts_list_error"] = str(ve)
            render()
            return
        state["debts_list_error"] = ""
        state["debt_total"] = str(principal)
        state["interest_rate"] = str(rate)
        state["interest_term"] = pp
        state["installment_count"] = str(n)
        state["first_due_date"] = rows[0]["due"].isoformat()
        state["schedule_result"] = {"rows": rows, "summary": summary}
        state["result_back_screen"] = "debts_list"
        state["result_view_intro"] = _result_intro_for_saved_schedule(itype)
        state["result_back_label"] = "กลับไปรายการหนี้"
        state["result_interest_rate_basis"] = rb
        go("result")

    def on_open_debts_crud(_: ft.ControlEvent) -> None:
        if state.get("user_id") is None:
            set_status("กรุณาเข้าสู่ระบบก่อน", True)
            render()
            return
        set_status("", False)
        go("debts_list")

    def logout_user(_: ft.ControlEvent) -> None:
        state["user_id"] = None
        state["username"] = ""
        state["debts_cache"] = []
        state["debts_list_error"] = ""
        state["schedule_result"] = None
        state["status_message"] = ""
        state["status_is_error"] = False
        state["editing_debt_id"] = None
        state["debt_form_error"] = ""
        state["debt_form_is_error"] = False
        for key in (
            "login_username",
            "login_password",
            "signup_username",
            "signup_password",
        ):
            try:
                controls[key].value = ""
            except Exception:
                pass
        try:
            controls["debt_total"].value = ""
            controls["interest_rate"].value = "7.5"
            controls["interest_term"].value = "month"
            controls["installment_count"].value = "12"
            controls["first_due_date"].value = date.today().isoformat()
        except Exception:
            pass
        try:
            controls["api_debt_name"].value = ""
            controls["api_debt_principal"].value = ""
            controls["api_debt_interest_rate"].value = "7.5"
            controls["api_debt_interest_rate_basis"].value = "year"
            controls["api_debt_interest_type"].value = "reducing"
            controls["api_debt_payment_period"].value = "month"
            controls["api_debt_installments"].value = "12"
            controls["api_debt_start_date"].value = date.today().isoformat()
            state["_api_pay_period"] = "month"
        except Exception:
            pass
        go("login")

    def open_debt_add(_: ft.ControlEvent) -> None:
        state["editing_debt_id"] = None
        controls["api_debt_name"].value = ""
        controls["api_debt_principal"].value = ""
        controls["api_debt_interest_rate"].value = "7.5"
        controls["api_debt_interest_rate_basis"].value = "year"
        controls["api_debt_interest_type"].value = "reducing"
        controls["api_debt_payment_period"].value = "month"
        controls["api_debt_installments"].value = "12"
        controls["api_debt_start_date"].value = date.today().isoformat()
        state["_api_pay_period"] = "month"
        set_debt_form_status("", False)
        go("debt_form")

    def open_debt_edit(debt_id: int) -> None:
        try:
            d = get_debt(debt_id)
            uid = state.get("user_id")
            if uid is not None and int(d.get("user_id", -1)) != int(uid):
                state["debts_list_error"] = "ไม่มีสิทธิ์แก้ไขรายการนี้"
                go("debts_list")
                return
            controls["api_debt_name"].value = str(d.get("debt_name", ""))
            controls["api_debt_principal"].value = format_money_decimal_display(d.get("principal"))
            controls["api_debt_interest_rate"].value = str(d.get("interest_rate", ""))
            controls["api_debt_interest_rate_basis"].value = str(d.get("interest_rate_basis", "year"))
            controls["api_debt_interest_type"].value = str(d.get("interest_type", "reducing"))
            _pp = _norm_freq_key(d.get("payment_period", "month"), default="month")
            controls["api_debt_payment_period"].value = _pp
            state["_api_pay_period"] = _pp
            controls["api_debt_installments"].value = str(d.get("total_installments", ""))
            sd = d.get("start_date", "")
            controls["api_debt_start_date"].value = str(sd)[:10] if sd else date.today().isoformat()
            state["editing_debt_id"] = debt_id
            set_debt_form_status("", False)
            go("debt_form")
        except Exception as ex:
            state["debts_list_error"] = _api_failure_message(ex)
            go("debts_list")

    def save_api_debt(_: ft.ControlEvent) -> None:
        uid = state.get("user_id")
        if uid is None:
            set_debt_form_status("กรุณาเข้าสู่ระบบก่อน", True)
            render()
            return
        name = (controls["api_debt_name"].value or "").strip()
        if not name:
            set_debt_form_status("กรุณากรอกชื่อรายการ", True)
            render()
            return
        try:
            principal = _to_decimal(strip_money_input(controls["api_debt_principal"].value or "0"))
            rate = _to_decimal(controls["api_debt_interest_rate"].value or "0")
            n = int(strip_money_input(controls["api_debt_installments"].value or ""))
            start = datetime.strptime((controls["api_debt_start_date"].value or "").strip(), "%Y-%m-%d").date()
        except (InvalidOperation, ValueError):
            set_debt_form_status("กรุณากรอกตัวเลขและวันที่ให้ถูกต้อง", True)
            render()
            return
        if principal <= 0:
            set_debt_form_status("เงินต้นต้องมากกว่า 0", True)
            render()
            return
        if rate < 0 or n < 1:
            set_debt_form_status("ดอกเบี้ยและจำนวนงวดไม่ถูกต้อง", True)
            render()
            return
        itype = controls["api_debt_interest_type"].value or "reducing"
        rb = _norm_freq_key(controls["api_debt_interest_rate_basis"].value, default="year")
        if rb not in ("week", "month", "year"):
            rb = "year"
        pp = _effective_pay_period(controls["api_debt_payment_period"], "_api_pay_period", "month")
        try:
            if state.get("editing_debt_id"):
                update_debt(
                    int(state["editing_debt_id"]),
                    {
                        "debt_name": name,
                        "principal": float(principal),
                        "interest_rate": float(rate),
                        "interest_rate_basis": rb,
                        "payment_period": pp,
                        "interest_type": itype,
                        "total_installments": n,
                        "start_date": start.isoformat(),
                    },
                )
            else:
                create_debt(
                    {
                        "user_id": int(uid),
                        "debt_name": name,
                        "principal": float(principal),
                        "interest_rate": float(rate),
                        "interest_rate_basis": rb,
                        "payment_period": pp,
                        "interest_type": itype,
                        "total_installments": n,
                        "start_date": start.isoformat(),
                    }
                )
            state["editing_debt_id"] = None
            set_debt_form_status("", False)
            go("debts_list")
        except Exception as ex:
            set_debt_form_status(_api_failure_message(ex), True)
            render()

    def cancel_debt_form(_: ft.ControlEvent) -> None:
        state["editing_debt_id"] = None
        go("debts_list")

    def _safe_page_update(*ctrls: ft.Control) -> None:
        """หลัง WebSocket ตัด การ update จะล้ม — กดไม่ให้ traceback ล้น + หยุดลูป GIF."""
        if not state.get("_session_alive", True):
            return
        try:
            if ctrls:
                page.update(*ctrls)
            else:
                page.update()
        except (AttributeError, OSError, RuntimeError):
            state["_session_alive"] = False
            state["bg_anim_running"] = False

    def ask_delete_debt(debt_id: int) -> None:
        # Flet เวอร์ชันใหม่: ต้องใช้ show_dialog — การตั้ง page.dialog บนเว็บมักไม่แสดงกล่องยืนยัน (กดแล้วไม่เกิดอะไร)
        def _close_dialog() -> None:
            if hasattr(page, "pop_dialog"):
                page.pop_dialog()
            else:
                page.dialog = None
                _safe_page_update()

        def close(_: ft.ControlEvent) -> None:
            _close_dialog()

        def do_delete(_: ft.ControlEvent) -> None:
            _close_dialog()
            delete_err: str | None = None
            try:
                delete_debt(debt_id)
            except Exception as ex:
                delete_err = _api_failure_message(ex)
            refresh_debts_list()
            if delete_err:
                state["debts_list_error"] = delete_err
                short = delete_err if len(delete_err) <= 320 else delete_err[:317] + "…"
                page.snack_bar = ft.SnackBar(
                    ft.Text(short, selectable=True),
                    bgcolor="#3D181C",
                    duration=ft.Duration(milliseconds=14_000),
                )
                page.snack_bar.open = True
            render()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("ยืนยันการลบ"),
            content=ft.Text(
                "กดปุ่ม «ลบ» เพื่อยืนยันว่าต้องการลบรายการหนี้นี้"
            ),
            actions=[
                ft.TextButton("ยกเลิก", on_click=close),
                ft.ElevatedButton(
                    "ลบ",
                    bgcolor="#9B2C2C",
                    color=TEXT_LIGHT,
                    on_click=do_delete,
                ),
            ],
        )
        if hasattr(page, "show_dialog"):
            page.show_dialog(dlg)
        else:
            page.dialog = dlg
            dlg.open = True
            _safe_page_update()

    async def _bg_gif_loop() -> None:
        try:
            await asyncio.sleep(0.05)
            while state.get("bg_anim_running") and state.get("_session_alive", True):
                frames = state.get("bg_gif_frames") or []
                delays = state.get("bg_gif_delays") or []
                img = state.get("bg_anim_img")
                if not frames or img is None:
                    await asyncio.sleep(0.2)
                    continue
                idx = int(state.get("bg_gif_frame_idx", 0))
                idx = (idx + 1) % len(frames)
                state["bg_gif_frame_idx"] = idx
                img.src = frames[idx]
                # เว็บ: อัปเดตทั้งหน้า + เปลี่ยน key บังคับให้ Flutter วาดรูปใหม่ (renderer แบบ auto มักไม่อัปเดตแค่ src)
                if bool(state.get("_gif_web_anim")):
                    img.key = idx
                    _safe_page_update()
                else:
                    _safe_page_update(img)
                d = delays[idx % len(delays)] if delays else 100
                slow_web = bool(state.get("_gif_web_anim"))
                lo = 0.075 if slow_web else 0.04
                hi = 0.48 if slow_web else 0.4
                await asyncio.sleep(max(lo, min(d / 1000.0, hi)))
        except Exception as ex:
            print(f"[Debt Manager] GIF frame loop error: {ex!r}")

    def render() -> None:
        pw = float(page.width or 0)
        ph = float(page.height or 0)
        content_width = layout_content_width(pw)
        _mobile = layout_mobile_breakpoint(pw)

        if state["screen"] == "login":
            inner = build_auth_body("login", content_width)
            body = ft.Container(
                content=inner,
                width=content_width,
                transform=_auth_transform_rotate_y(0),
                clip_behavior=ft.ClipBehavior.NONE,
            )
            controls["auth_flip_wrap"] = body
        elif state["screen"] == "signup":
            inner = build_auth_body("signup", content_width)
            body = ft.Container(
                content=inner,
                width=content_width,
                transform=_auth_transform_rotate_y(0),
                clip_behavior=ft.ClipBehavior.NONE,
            )
            controls["auth_flip_wrap"] = body
        elif state["screen"] == "dashboard":
            body = build_dashboard_view(
                content_width=content_width,
                username=state["username"],
                mobile=_mobile,
                debt_total_field=controls["debt_total"],
                debt_editing=state["debt_total_editing"],
                on_edit_debt=on_edit_debt,
                on_save_debt=on_save_debt,
                on_cancel_debt=on_cancel_debt,
                interest_rate_field=controls["interest_rate"],
                interest_term_dropdown=controls["interest_term"],
                installment_count_field=controls["installment_count"],
                first_due_date_field=controls["first_due_date"],
                status_message=state["status_message"],
                status_is_error=state["status_is_error"],
                on_calculate=go_result,
                on_open_debts_crud=on_open_debts_crud,
                on_logout=logout_user,
            )
        elif state["screen"] == "result":
            sr = state.get("schedule_result")
            if not sr:
                body = ft.Column(
                    [
                        ft.Text(
                            "ไม่มีผลการคำนวณ — กลับไปกรอกข้อมูลที่หน้าหลัก",
                            color=TEXT_SOFT,
                        ),
                        ft.ElevatedButton(
                            "กลับ",
                            bgcolor=GREEN_DARK,
                            color=TEXT_LIGHT,
                            on_click=lambda _: go("dashboard"),
                        ),
                    ],
                    tight=True,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            else:
                body = build_result_view(
                    content_width=content_width,
                    mobile=_mobile,
                    debt_total=state["debt_total"],
                    interest_rate=state["interest_rate"],
                    interest_term=state["interest_term"],
                    installment_count=state["installment_count"],
                    first_due_label=state["first_due_date"],
                    rows=sr["rows"],
                    summary=sr["summary"],
                    on_back=lambda _: go(state.get("result_back_screen", "dashboard")),
                    interest_rate_basis=state.get("result_interest_rate_basis"),
                    schedule_intro=state.get("result_view_intro"),
                    back_button_text=state.get("result_back_label"),
                )
        elif state["screen"] == "debts_list":
            body = build_debts_list_view(
                content_width=content_width,
                mobile=_mobile,
                debts=state.get("debts_cache") or [],
                list_error=state.get("debts_list_error") or "",
                on_add=open_debt_add,
                on_edit=open_debt_edit,
                on_delete=ask_delete_debt,
                on_calculate=preview_debt_from_list,
                on_back=lambda _: go("dashboard"),
            )
        elif state["screen"] == "debt_form":
            body = build_debt_form_view(
                content_width=content_width,
                mobile=_mobile,
                is_edit=state.get("editing_debt_id") is not None,
                debt_name_field=controls["api_debt_name"],
                principal_field=controls["api_debt_principal"],
                interest_rate_field=controls["api_debt_interest_rate"],
                interest_rate_basis_dropdown=controls["api_debt_interest_rate_basis"],
                interest_type_dropdown=controls["api_debt_interest_type"],
                payment_period_dropdown=controls["api_debt_payment_period"],
                installments_field=controls["api_debt_installments"],
                start_date_field=controls["api_debt_start_date"],
                status_message=state.get("debt_form_error") or "",
                status_is_error=bool(state.get("debt_form_is_error")),
                on_save=save_api_debt,
                on_cancel=cancel_debt_form,
                on_calculate=preview_debt_form_schedule,
            )
        else:
            body = ft.Text(f"ไม่รู้จักหน้า: {state.get('screen')!r}", color=TEXT_SOFT)

        # ขนาด viewport ชัดเจน — บนมือถือเว็บถ้าไม่กำหนด ภาพพื้นหลังมักได้ 0x0 จนไม่เห็น GIF
        vp_w = float(page.width) if page.width and float(page.width) > 0 else 390.0
        vp_h = float(page.height) if page.height and float(page.height) > 0 else 844.0
        bg_src = _background_src() if _use_background_gif(page) else ""
        use_manual = _use_manual_gif_frames(page)
        web_client = bool(getattr(page, "web", False))
        state["_gif_web_anim"] = web_client
        # เว็บ = เฟรม JPEG เล็ก (ทุกเบราว์เซอร์) · แอปหน้าต่าง = PNG เต็ม
        _gif_pack = "w" if web_client else "d"
        if state.get("_gif_pack_kind") != _gif_pack:
            state["bg_anim_running"] = False
            state["_gif_pack_kind"] = _gif_pack
            state["bg_gif_frames"] = None
            state["bg_gif_delays"] = None
            state["bg_anim_img"] = None
            state["_bg_gif_future"] = None

        if bg_src and use_manual:
            full_path = os.path.join(ASSETS_DIR, bg_src)
            if state.get("bg_gif_frames") is None:
                loaded = _load_gif_animation_frames(
                    full_path,
                    max_frames=48,
                    max_side=480,
                    lite_web=web_client,
                )
                if loaded:
                    state["bg_gif_frames"], state["bg_gif_delays"] = loaded
                    state["bg_gif_frame_idx"] = 0
                    print(
                        f"[Debt Manager] GIF พื้นหลัง: โหลด {len(state['bg_gif_frames'])} เฟรม "
                        f"({'เว็บ: JPEG ย่อ' if web_client else 'แอปหน้าต่าง: PNG'})"
                    )
                else:
                    state["bg_gif_frames"] = []
                    _why = _gif_load_failure_reason(full_path)
                    print(f"[Debt Manager] GIF พื้นหลัง: ไม่แยกเฟรมได้ — {_why}")

            if state.get("bg_gif_frames"):
                if state.get("bg_anim_img") is None:
                    state["bg_anim_img"] = ft.Image(
                        src=state["bg_gif_frames"][0],
                        width=vp_w,
                        height=vp_h,
                        fit="cover",
                        gapless_playback=not web_client,
                        filter_quality=ft.FilterQuality.LOW,
                    )
                else:
                    anim = state["bg_anim_img"]
                    anim.width = vp_w
                    anim.height = vp_h
                    anim.gapless_playback = not web_client
                bg_layer = state["bg_anim_img"]
            else:
                bg_layer = _build_background_image(page, bg_src, vp_w, vp_h)
        else:
            state["bg_anim_running"] = False
            state["bg_gif_frames"] = None
            state["bg_gif_delays"] = None
            state["bg_anim_img"] = None
            state["_bg_gif_future"] = None
            if bg_src:
                bg_layer = _build_background_image(page, bg_src, vp_w, vp_h)
            else:
                bg_layer = ft.Container(width=vp_w, height=vp_h, bgcolor=BG_DARK)

        page.controls.clear()
        page.add(
            ft.Container(
                expand=True,
                padding=0,
                margin=0,
                content=ft.Stack(
                    expand=True,
                    fit=ft.StackFit.EXPAND,
                    controls=[
                        bg_layer,
                        ft.Container(
                            expand=True,
                            bgcolor=ft.Colors.with_opacity(0.72, BG_DARK),
                            padding=page_content_padding(pw, ph),
                            alignment=ft.Alignment(0, 0),
                            content=ft.Column(
                                [body],
                                expand=True,
                                scroll=ft.ScrollMode.AUTO,
                                alignment=ft.MainAxisAlignment.START,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                        ),
                    ],
                ),
            )
        )
        _safe_page_update()
        if use_manual and state.get("bg_gif_frames") and state.get("bg_anim_img"):
            state["bg_anim_running"] = True
            prev_fut = state.get("_bg_gif_future")
            need_new_loop = prev_fut is None or (
                isinstance(prev_fut, ConcurrentFuture) and prev_fut.done()
            )
            if need_new_loop:
                state["_bg_gif_future"] = page.run_task(_bg_gif_loop)
                print("[Debt Manager] เริ่มลูปสลับเฟรม GIF พื้นหลัง")

    _last_vp = [0.0, 0.0]

    def on_resize(_: ft.ControlEvent) -> None:
        w = float(page.width or 0)
        h = float(page.height or 0)
        if w < 80 or h < 80:
            return
        dw = abs(w - _last_vp[0])
        dh = abs(h - _last_vp[1])
        if _last_vp[0] > 0 and dw < 16 and dh < 16:
            return
        _last_vp[0], _last_vp[1] = w, h
        render()

    def _make_pay_period_sync(state_key: str, default: str):
        def _h(e: ft.ControlEvent) -> None:
            state[state_key] = _norm_freq_key(getattr(e.control, "value", None), default=state.get(state_key, default))

        return _h

    controls["interest_term"].on_change = _make_pay_period_sync("_dash_pay_period", "month")
    controls["api_debt_payment_period"].on_change = _make_pay_period_sync("_api_pay_period", "month")
    controls["debt_total"].on_change = on_debt_total_change
    controls["api_debt_principal"].on_change = on_api_debt_principal_change
    controls["api_debt_interest_rate"].on_change = on_api_debt_interest_rate_change
    controls["api_debt_installments"].on_change = on_api_debt_installments_change

    attach_date_picker(
        page,
        controls["first_due_date"],
        help_text="วันครบกำหนดงวดแรก",
    )
    attach_date_picker(
        page,
        controls["api_debt_start_date"],
        help_text="วันเริ่มนับงวดแรก",
    )

    def _on_web_disconnect(_: ft.ControlEvent) -> None:
        state["bg_anim_running"] = False
        state["_session_alive"] = False

    def _on_web_close(_: ft.ControlEvent) -> None:
        state["bg_anim_running"] = False
        state["_session_alive"] = False

    def _on_web_connect(_: ft.ControlEvent) -> None:
        state["_session_alive"] = True

    page.on_disconnect = _on_web_disconnect
    page.on_close = _on_web_close
    page.on_connect = _on_web_connect
    page.on_resize = on_resize
    render()
    _last_vp[0] = float(page.width or 0)
    _last_vp[1] = float(page.height or 0)


if __name__ == "__main__":
    # แอปหน้าต่าง (Flet desktop) — ไม่ใช่เบราว์เซอร์; เว็บใช้ python run_flet_web.py
    ft.run(main, assets_dir=ASSETS_DIR)

