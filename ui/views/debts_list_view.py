from __future__ import annotations

import flet as ft

from ui.theme import (
    ERROR_LIGHT,
    GREEN,
    GREEN_DARK,
    TEXT_LIGHT,
    TEXT_SOFT,
    format_money_decimal_display,
    wrapped_card,
)


def _status_th(s: str) -> str:
    return {"active": "กำลังผ่อนอยู่", "paid": "ปิดยอดแล้ว"}.get(s, s)


def build_debts_list_view(
    content_width: float,
    mobile: bool,
    debts: list[dict],
    list_error: str,
    on_add,
    on_edit,
    on_delete,
    on_calculate,
    on_back,
) -> ft.Control:
    row_width = content_width - 40

    def card_for(d: dict) -> ft.Container:
        did = int(d["debt_id"])
        principal = format_money_decimal_display(d.get("principal"))
        end = str(d.get("end_date", ""))
        st = _status_th(str(d.get("status", "")))
        name = str(d.get("debt_name", "")) or "(ไม่มีชื่อ)"

        def on_tap_edit(_: ft.ControlEvent) -> None:
            on_edit(did)

        def on_tap_delete(_: ft.ControlEvent) -> None:
            on_delete(did)

        def on_tap_calc(_: ft.ControlEvent) -> None:
            on_calculate(did)

        _btn_pad = ft.padding.symmetric(horizontal=14, vertical=10)
        _shape = ft.RoundedRectangleBorder(radius=8)
        actions = ft.Row(
            [
                ft.OutlinedButton(
                    "คำนวณ",
                    height=44,
                    on_click=on_tap_calc,
                    style=ft.ButtonStyle(
                        color=GREEN,
                        side=ft.BorderSide(1, GREEN_DARK),
                        shape=_shape,
                        padding=_btn_pad,
                    ),
                ),
                ft.OutlinedButton(
                    "แก้ไข",
                    height=44,
                    on_click=on_tap_edit,
                    style=ft.ButtonStyle(
                        color=TEXT_LIGHT,
                        side=ft.BorderSide(1, GREEN_DARK),
                        shape=_shape,
                        padding=_btn_pad,
                    ),
                ),
                ft.ElevatedButton(
                    "ลบ",
                    height=44,
                    bgcolor="#6B2222",
                    color=TEXT_LIGHT,
                    on_click=on_tap_delete,
                    style=ft.ButtonStyle(shape=_shape, padding=_btn_pad),
                ),
            ],
            spacing=10,
            wrap=True,
        )
        if mobile:
            body = ft.Column(
                [
                    ft.Text(name, weight=ft.FontWeight.W_600, color=GREEN, size=16),
                    ft.Text(f"ยอดหนี้ตั้งต้น {principal} บาท", color=TEXT_LIGHT, size=13),
                    ft.Text(st, color=TEXT_SOFT, size=13),
                    ft.Text(
                        f"ผ่อนครบประมาณวันที่ {end}" if end else "—",
                        color=TEXT_SOFT,
                        size=12,
                    ),
                    actions,
                ],
                spacing=6,
                tight=True,
            )
        else:
            body = ft.Column(
                [
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text(name, weight=ft.FontWeight.W_600, color=GREEN, size=16),
                                    ft.Text(
                                        f"ยอดตั้งต้น {principal} บาท · {st} · ครบประมาณ {end}",
                                        color=TEXT_SOFT,
                                        size=13,
                                    ),
                                ],
                                expand=True,
                                spacing=2,
                            ),
                            actions,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    ),
                ],
                tight=True,
            )
        return ft.Container(
            content=body,
            padding=12,
            border=ft.border.all(1, GREEN_DARK),
            border_radius=10,
            bgcolor="#0A120A",
            width=row_width,
        )

    err: ft.Control | None
    if list_error:
        err = ft.Container(
            width=row_width,
            padding=12,
            bgcolor="#2A1518",
            border=ft.border.all(1, ERROR_LIGHT),
            border_radius=8,
            content=ft.Column(
                [
                    ft.Text(
                        "แจ้งเตือน (ลบหนี้ / โหลดรายการ)",
                        size=12,
                        weight=ft.FontWeight.W_600,
                        color=ERROR_LIGHT,
                    ),
                    ft.Text(
                        list_error,
                        size=13,
                        color="#FFCCCC",
                        width=row_width - 24,
                        max_lines=20,
                        selectable=True,
                    ),
                ],
                spacing=6,
                tight=True,
            ),
        )
    else:
        err = None

    if not debts and not list_error:
        empty = ft.Column(
            [
                ft.Text(
                    "ยังไม่มีรายการหนี้",
                    color=TEXT_LIGHT,
                    size=15,
                    text_align=ft.TextAlign.CENTER,
                    width=row_width,
                ),
                ft.Text(
                    "กดปุ่ม «เพิ่มหนี้รายใหม่» ด้านบนเพื่อบันทึกหนี้ที่ต้องการติดตาม เช่น ค่างวดรถ บ้าน หรือบัตรเครดิต",
                    color=TEXT_SOFT,
                    size=13,
                    text_align=ft.TextAlign.CENTER,
                    width=row_width,
                ),
            ],
            spacing=8,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
        body_list: list[ft.Control] = [empty]
    else:
        body_list = [card_for(d) for d in debts]

    top_actions = ft.Row(
        [
            ft.OutlinedButton(
                "← กลับหน้าหลัก",
                on_click=on_back,
                style=ft.ButtonStyle(
                    color=TEXT_SOFT,
                    side=ft.BorderSide(1, GREEN_DARK),
                    shape=ft.RoundedRectangleBorder(radius=6),
                ),
            ),
            ft.ElevatedButton(
                "เพิ่มหนี้รายใหม่",
                bgcolor=GREEN_DARK,
                color=TEXT_LIGHT,
                on_click=on_add,
            ),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        width=row_width,
        wrap=True,
    )

    intro = ft.Column(
        [
            ft.Text(
                "หน้านี้ใช้เก็บรายการหนี้ที่คุณบันทึกไว้ในระบบ",
                size=14,
                color=TEXT_LIGHT,
                text_align=ft.TextAlign.CENTER,
                width=row_width,
            ),
            ft.Text(
                "ดูยอดตั้งต้น สถานะการผ่อน และวันที่คาดว่าจะผ่อนครบ — แก้ไขหรือลบได้ทุกรายการ",
                size=12,
                color=TEXT_SOFT,
                text_align=ft.TextAlign.CENTER,
                width=row_width,
            ),
        ],
        spacing=4,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    return wrapped_card(
        ft.Column(
            [
                ft.Text(
                    "รายการหนี้ที่บันทึกไว้",
                    size=22,
                    weight=ft.FontWeight.BOLD,
                    color=GREEN,
                    text_align=ft.TextAlign.CENTER,
                    width=row_width,
                ),
                intro,
                top_actions,
                err if err is not None else ft.Container(height=0),
                *body_list,
            ],
            spacing=12,
            tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
        ),
        width=content_width,
    )
