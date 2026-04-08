"""ระยะขอบและความกว้างการ์ดหลัก — ใช้ทุกหน้าให้ responsive เว้นขอบจอสม่ำเสมอ."""

from __future__ import annotations

import flet as ft

# ความกว้างการ์ดสูงสุด (จอใหญ่ไม่ให้บรรทัดยาวเกินไป)
_MAX_CARD_WIDTH = 720.0
# ความกว้างขั้นต่ำของโซนเนื้อหา (มือถือแคบมาก)
_MIN_INNER_WIDTH = 260.0


def layout_horizontal_margin(page_width: float) -> float:
    """เว้นซ้าย-ขวาจากขอบจอ (px) — มือถือเว้นมากขึ้น ไม่ให้ชิดขอบ."""
    if page_width <= 0:
        return 22.0
    if page_width < 480:
        return float(max(20, min(36, page_width * 0.075)))
    # จอใหญ่ ~4.8% จำกัด 16–40 px
    return float(max(16, min(40, page_width * 0.048)))


def layout_vertical_margin(page_height: float) -> float:
    """เว้นบน-ล่างเล็กน้อยให้ไม่ชิดขอบจอ."""
    if page_height <= 0:
        return 16.0
    return float(max(12, min(32, page_height * 0.02)))


def layout_content_width(page_width: float) -> float:
    """ความกว้างที่ใช้กับ wrapped_card / ฟอร์มหลัก (หักขอบซ้ายขวาแล้ว)."""
    pw = page_width if page_width > 0 else 390.0
    m = layout_horizontal_margin(pw)
    inner = pw - 2.0 * m
    return float(min(max(inner, _MIN_INNER_WIDTH), _MAX_CARD_WIDTH))


def layout_mobile_breakpoint(page_width: float) -> bool:
    """จอแคบ (มือถือ / หน้าต่างแคบ) — ใช้จัดปุ่มแถว / wrap."""
    return (page_width if page_width > 0 else 390.0) <= 700.0


def page_content_padding(page_width: float, page_height: float) -> ft.Padding:
    """padding รอบโซนเลื่อนทั้งหมด — ซ้ายขวา + บนล่าง."""
    return ft.padding.only(
        left=layout_horizontal_margin(page_width),
        right=layout_horizontal_margin(page_width),
        top=layout_vertical_margin(page_height),
        bottom=layout_vertical_margin(page_height),
    )
