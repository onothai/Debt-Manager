from __future__ import annotations

import flet as ft

from ui.theme import (
    CARD_DARK,
    GREEN,
    GREEN_DARK,
    TEXT_LIGHT,
    TEXT_SOFT,
    form_field_caption,
    status_text,
    wrapped_card,
)

_FORM_TEXT_SIZE = 14


def build_debt_form_view(
    content_width: float,
    mobile: bool,
    is_edit: bool,
    debt_name_field: ft.TextField,
    principal_field: ft.TextField,
    interest_rate_field: ft.TextField,
    interest_rate_basis_dropdown: ft.Dropdown,
    interest_type_dropdown: ft.Dropdown,
    payment_period_dropdown: ft.Dropdown,
    installments_field: ft.TextField,
    start_date_field: ft.TextField,
    status_message: str,
    status_is_error: bool,
    on_save,
    on_cancel,
    on_calculate,
) -> ft.Control:
    row_width = content_width - 40
    narrow = row_width < 360
    _h = 48
    half_w = max(120, int((row_width - 12) / 2))

    for c in (
        debt_name_field,
        principal_field,
        interest_rate_field,
        installments_field,
        start_date_field,
    ):
        c.label = ""
    interest_rate_basis_dropdown.label = ""
    interest_type_dropdown.label = ""
    payment_period_dropdown.label = ""

    _hint_style = ft.TextStyle(color=TEXT_SOFT, size=13)
    _input_ts = ft.TextStyle(color=TEXT_LIGHT, size=_FORM_TEXT_SIZE)

    debt_name_field.hint_text = "เช่น ค่างวดรถ, บัตรเครดิต A"
    principal_field.hint_text = "เช่น 500,000"
    interest_rate_field.hint_text = "เช่น 7.5"
    installments_field.hint_text = "เช่น 12 หรือ 60"
    start_date_field.hint_text = "แตะเพื่อเลือกจากปฏิทิน"

    for c in (
        debt_name_field,
        principal_field,
        interest_rate_field,
        installments_field,
        start_date_field,
    ):
        c.border_color = GREEN_DARK
        c.color = TEXT_LIGHT
        c.focused_border_color = GREEN
        c.height = _h
        c.border_radius = 6
        c.dense = False
        c.bgcolor = CARD_DARK
        c.fill_color = CARD_DARK
        c.multiline = False
        c.min_lines = 1
        c.max_lines = 1
        c.text_style = _input_ts
        c.hint_style = _hint_style

    interest_type_dropdown.border_color = GREEN_DARK
    interest_type_dropdown.color = TEXT_LIGHT
    interest_type_dropdown.focused_border_color = GREEN
    interest_type_dropdown.height = _h
    interest_type_dropdown.bgcolor = CARD_DARK
    interest_rate_basis_dropdown.border_color = GREEN_DARK
    interest_rate_basis_dropdown.color = TEXT_LIGHT
    interest_rate_basis_dropdown.focused_border_color = GREEN
    interest_rate_basis_dropdown.height = _h
    interest_rate_basis_dropdown.bgcolor = CARD_DARK
    payment_period_dropdown.border_color = GREEN_DARK
    payment_period_dropdown.color = TEXT_LIGHT
    payment_period_dropdown.focused_border_color = GREEN
    payment_period_dropdown.height = _h
    payment_period_dropdown.bgcolor = CARD_DARK

    title = "แก้ไขรายการหนี้" if is_edit else "เพิ่มรายการหนี้"
    hint = "บันทึกลง MariaDB (สร้างงวดในตาราง installment อัตโนมัติ)"

    _cap_m = ft.TextAlign.CENTER
    _cap_d = ft.TextAlign.START
    _sp = 6

    if mobile:
        for c in (debt_name_field, principal_field, interest_rate_field, installments_field, start_date_field):
            c.width = row_width
        interest_rate_basis_dropdown.width = row_width
        interest_type_dropdown.width = row_width
        payment_period_dropdown.width = row_width
        _date_lbl = (
            "วันเริ่มงวดแรก (แตะเลือกวันที่)"
            if narrow
            else "วันเริ่มนับงวดแรก (แตะช่องเพื่อเลือกจากปฏิทิน)"
        )
        form_rows: list[ft.Control] = [
            ft.Column(
                [form_field_caption("ชื่อรายการ", row_width, text_align=_cap_m), debt_name_field],
                spacing=_sp,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                width=row_width,
            ),
            ft.Column(
                [form_field_caption("เงินต้น (บาท)", row_width, text_align=_cap_m), principal_field],
                spacing=_sp,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                width=row_width,
            ),
            ft.Column(
                [form_field_caption("อัตรา %", row_width, text_align=_cap_m), interest_rate_field],
                spacing=_sp,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                width=row_width,
            ),
            ft.Column(
                [form_field_caption("อัตรานี้นับต่อ", row_width, text_align=_cap_m), interest_rate_basis_dropdown],
                spacing=_sp,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                width=row_width,
            ),
            ft.Column(
                [form_field_caption("คิดดอกจากอะไร", row_width, text_align=_cap_m), interest_type_dropdown],
                spacing=_sp,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                width=row_width,
            ),
            ft.Column(
                [form_field_caption("จำนวนงวด", row_width, text_align=_cap_m), installments_field],
                spacing=_sp,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                width=row_width,
            ),
            ft.Column(
                [form_field_caption("ผ่อนทุก", row_width, text_align=_cap_m), payment_period_dropdown],
                spacing=_sp,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                width=row_width,
            ),
            ft.Column(
                [form_field_caption(_date_lbl, row_width, text_align=_cap_m), start_date_field],
                spacing=_sp,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                width=row_width,
            ),
        ]
    else:
        debt_name_field.width = row_width
        principal_field.width = row_width
        interest_rate_field.width = half_w
        interest_rate_basis_dropdown.width = half_w
        interest_type_dropdown.width = half_w
        installments_field.width = half_w
        payment_period_dropdown.width = half_w
        start_date_field.width = half_w
        form_rows = [
            ft.Column(
                [form_field_caption("ชื่อรายการ", row_width, text_align=_cap_d), debt_name_field],
                spacing=_sp,
                width=row_width,
            ),
            ft.Column(
                [form_field_caption("เงินต้น (บาท)", row_width, text_align=_cap_d), principal_field],
                spacing=_sp,
                width=row_width,
            ),
            ft.Row(
                [
                    ft.Column(
                        [form_field_caption("อัตรา %", half_w, text_align=_cap_d), interest_rate_field],
                        spacing=_sp,
                        width=half_w,
                    ),
                    ft.Column(
                        [
                            form_field_caption("อัตรานี้นับต่อ", half_w, text_align=_cap_d),
                            interest_rate_basis_dropdown,
                        ],
                        spacing=_sp,
                        width=half_w,
                    ),
                ],
                spacing=12,
                width=row_width,
            ),
            ft.Row(
                [
                    ft.Column(
                        [form_field_caption("คิดดอกจากอะไร", half_w, text_align=_cap_d), interest_type_dropdown],
                        spacing=_sp,
                        width=half_w,
                    ),
                    ft.Column(
                        [form_field_caption("จำนวนงวด", half_w, text_align=_cap_d), installments_field],
                        spacing=_sp,
                        width=half_w,
                    ),
                ],
                spacing=12,
                width=row_width,
            ),
            ft.Row(
                [
                    ft.Column(
                        [form_field_caption("ผ่อนทุก", half_w, text_align=_cap_d), payment_period_dropdown],
                        spacing=_sp,
                        width=half_w,
                    ),
                    ft.Column(
                        [
                            form_field_caption("วันเริ่มงวดแรก (แตะเลือกวันที่)", half_w, text_align=_cap_d),
                            start_date_field,
                        ],
                        spacing=_sp,
                        width=half_w,
                    ),
                ],
                spacing=12,
                width=row_width,
            ),
        ]

    _cancel_style = ft.ButtonStyle(
        color=TEXT_SOFT,
        side=ft.BorderSide(1, GREEN_DARK),
        shape=ft.RoundedRectangleBorder(radius=8),
        padding=ft.padding.symmetric(horizontal=14, vertical=12),
    )
    _save_style = ft.ButtonStyle(
        shape=ft.RoundedRectangleBorder(radius=8),
        padding=ft.padding.symmetric(horizontal=18, vertical=12),
    )
    _calc_style = ft.ButtonStyle(
        color=GREEN,
        side=ft.BorderSide(1, GREEN_DARK),
        shape=ft.RoundedRectangleBorder(radius=8),
        padding=ft.padding.symmetric(horizontal=14, vertical=12),
    )
    if mobile:
        form_actions = ft.Column(
            [
                ft.OutlinedButton(
                    "ยกเลิก",
                    width=row_width,
                    on_click=on_cancel,
                    style=_cancel_style,
                ),
                ft.OutlinedButton(
                    "คำนวณ",
                    width=row_width,
                    on_click=on_calculate,
                    style=_calc_style,
                ),
                ft.ElevatedButton(
                    "บันทึก",
                    width=row_width,
                    bgcolor=GREEN_DARK,
                    color=TEXT_LIGHT,
                    on_click=on_save,
                    style=_save_style,
                ),
            ],
            spacing=10,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            width=row_width,
        )
    else:
        form_actions = ft.Row(
            [
                ft.OutlinedButton("ยกเลิก", on_click=on_cancel, style=_cancel_style),
                ft.OutlinedButton("คำนวณ", on_click=on_calculate, style=_calc_style),
                ft.ElevatedButton(
                    "บันทึก",
                    bgcolor=GREEN_DARK,
                    color=TEXT_LIGHT,
                    on_click=on_save,
                    style=_save_style,
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=12,
            width=row_width,
        )

    _title_size = 20 if narrow else 22

    return wrapped_card(
        ft.Column(
            [
                ft.Text(
                    title,
                    size=_title_size,
                    weight=ft.FontWeight.BOLD,
                    color=GREEN,
                    text_align=ft.TextAlign.CENTER,
                    width=row_width,
                    max_lines=2,
                ),
                ft.Text(
                    hint,
                    size=12,
                    color=TEXT_SOFT,
                    width=row_width,
                    text_align=ft.TextAlign.CENTER,
                    max_lines=4,
                ),
                *form_rows,
                status_text(status_message, status_is_error, width=row_width),
                form_actions,
            ],
            spacing=10,
            tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
        ),
        width=content_width,
    )
