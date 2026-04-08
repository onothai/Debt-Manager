from __future__ import annotations

from decimal import Decimal, InvalidOperation

import flet as ft

BG_DARK = "#0A0E0A"
CARD_DARK = "#111A11"
GREEN = "#5BE67A"
GREEN_DARK = "#1F8F45"
TEXT_LIGHT = "#E8FFE9"
TEXT_SOFT = "#9FD3A9"
ERROR_LIGHT = "#FF9B9B"

# Signup — โทนทอง/อำพัน (แยกจาก Login เขียวให้รู้ทันทีว่าอยู่หน้าไหน)
SIGNUP_CARD_BG = "#15110E"
SIGNUP_BORDER = "#8B5A1E"
SIGNUP_ACCENT = "#FFC14A"
SIGNUP_ACCENT_DARK = "#B8730A"
SIGNUP_TEXT_LIGHT = "#FFF6E8"
SIGNUP_TEXT_SOFT = "#D4B896"

# Keep theme minimal for broader Flet version compatibility.
APP_THEME = ft.Theme()


def strip_money_input(s: str) -> str:
    """ตัดคอมมา/ช่องว่างก่อนส่งเข้า Decimal หรือ API — ไม่กระทบ DB"""
    return (s or "").replace(",", "").replace(" ", "").strip()


def format_money_decimal_display(value) -> str:
    """แสดงตัวเลขด้วยคั่นหลักพัน (ใช้เฉพาะ UI)."""
    if value is None or value == "":
        return "0"
    try:
        d = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return "0"
    return _format_decimal_with_commas(d)


def _format_decimal_with_commas(d: Decimal) -> str:
    neg = d < 0
    d = abs(d)
    s = format(d, "f")
    if "." in s:
        ip, frac = s.split(".", 1)
        frac = frac.rstrip("0").rstrip(".")
    else:
        ip, frac = s, ""
    ip = ip.lstrip("-")
    int_digits = "".join(c for c in ip if c.isdigit())
    if not int_digits:
        int_digits = "0"
    n = int(int_digits)
    body = f"{n:,}"
    if neg:
        body = "-" + body
    if frac:
        return f"{body}.{frac}"
    return body


def format_money_typing_display(raw: str) -> str:
    """ระหว่างพิมพ์: จำกัดตัวเลข+จุดทศนิยมหนึ่งจุด แล้วใส่คอมมา."""
    raw = strip_money_input(raw)
    if not raw:
        return ""
    buf: list[str] = []
    dot = False
    for c in raw:
        if c.isdigit():
            buf.append(c)
        elif c == "." and not dot:
            buf.append(".")
            dot = True
    s = "".join(buf)
    if not s:
        return ""
    if s == ".":
        return "0."
    ends_dot = s.endswith(".") and s.count(".") == 1
    num_part = s[:-1] if ends_dot else s
    if not num_part:
        return "0." if ends_dot else "0"
    try:
        d = Decimal(num_part)
        out = format_money_decimal_display(d)
        return out + "." if ends_dot else out
    except (InvalidOperation, ValueError):
        return s


def format_integer_typing_display(raw: str) -> str:
    """จำนวนเต็มระหว่างพิมพ์ — คั่นหลักพันด้วยคอมมา (เช่น จำนวนงวด)."""
    digits = "".join(c for c in (raw or "") if c.isdigit())
    if not digits:
        return ""
    try:
        n = int(digits)
        if n > 999_999_999:
            n = int(digits[:9])
        return f"{n:,}"
    except ValueError:
        return digits


def form_field_caption(text: str, width: float | int, *, text_align: ft.TextAlign) -> ft.Text:
    """หัวข้อเหนือช่องกรอก — โทนเดียวกับหน้าคำนวณหนี้"""
    return ft.Text(
        text,
        size=13,
        color=TEXT_SOFT,
        width=width,
        text_align=text_align,
        max_lines=3,
    )


def status_text(message: str, is_error: bool = False, *, width: float | None = None) -> ft.Text:
    return ft.Text(
        message or "",
        color=ERROR_LIGHT if is_error else TEXT_SOFT,
        size=13,
        text_align=ft.TextAlign.CENTER,
        width=width,
        max_lines=12,
    )


def status_text_signup(message: str, is_error: bool = False, *, width: float | None = None) -> ft.Text:
    return ft.Text(
        message or "",
        color=ERROR_LIGHT if is_error else SIGNUP_TEXT_SOFT,
        size=13,
        text_align=ft.TextAlign.CENTER,
        width=width,
        max_lines=12,
    )


def wrapped_card(content: ft.Control, width: float, *, card_padding: float = 20) -> ft.Container:
    return ft.Container(
        width=width,
        bgcolor=CARD_DARK,
        border_radius=16,
        padding=card_padding,
        border=ft.border.all(1, GREEN_DARK),
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        content=content,
    )


def wrapped_signup_card(content: ft.Control, width: float) -> ft.Container:
    return ft.Container(
        width=width,
        bgcolor=SIGNUP_CARD_BG,
        border_radius=16,
        padding=20,
        border=ft.border.all(1, SIGNUP_BORDER),
        clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
        content=content,
    )
