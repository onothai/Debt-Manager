"""Attach Material calendar-only date picking to read-only TextField (YYYY-MM-DD)."""

from __future__ import annotations

from datetime import date, datetime

import flet as ft


def _parse_iso_date(value: str | None) -> date:
    raw = (value or "").strip()
    if not raw:
        return date.today()
    try:
        return date.fromisoformat(raw[:10])
    except ValueError:
        return date.today()


def _value_to_date(v: object | None) -> date | None:
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    try:
        return date.fromisoformat(str(v)[:10])
    except ValueError:
        return None


def attach_date_picker(
    page: ft.Page,
    text_field: ft.TextField,
    *,
    help_text: str = "เลือกวันที่",
    first_date: date | None = None,
    last_date: date | None = None,
) -> None:
    """Make field read-only; tap opens calendar dialog; value stays YYYY-MM-DD."""

    first = first_date or date(1900, 1, 1)
    last = last_date or date(2100, 12, 31)

    def _on_confirm(e: ft.ControlEvent) -> None:
        d = _value_to_date(e.control.value)
        if d is None:
            return
        text_field.value = d.isoformat()
        page.update()

    def _open(_: ft.ControlEvent) -> None:
        cur = _parse_iso_date(text_field.value)
        dp = ft.DatePicker(
            value=datetime.combine(cur, datetime.min.time()),
            first_date=datetime.combine(first, datetime.min.time()),
            last_date=datetime.combine(last, datetime.min.time()),
            entry_mode=ft.DatePickerEntryMode.CALENDAR_ONLY,
            help_text=help_text,
            cancel_text="ยกเลิก",
            confirm_text="ตกลง",
            on_change=_on_confirm,
        )
        page.show_dialog(dp)

    text_field.read_only = True
    text_field.show_cursor = False
    text_field.suffix_icon = ft.Icons.CALENDAR_TODAY
    text_field.on_click = _open
