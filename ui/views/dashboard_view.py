from __future__ import annotations

import flet as ft

from ui.theme import CARD_DARK, GREEN, GREEN_DARK, TEXT_LIGHT, TEXT_SOFT, status_text, wrapped_card

# ช่องกับปุ่มความสูงเดียวกัน — ไม่ใช้ label ลอยใน TextField
# ค่าเดียวกันทั้งช่องและปุ่ม (เคยขึ้น 56 เพื่อให้เสมอ — ถ้าอยากกะทัดรัดขึ้นใช้ 48)
_DEBT_ROW_MATCH_HEIGHT = 48
# ขนาดตัวอักษรปุ่มแก้ไข/บันทึก/ยกเลิก — ใช้ค่าเดียวกับ suffix «บาท»
_DEBT_ROW_TEXT_SIZE = 14


def _input_caption(text: str, width: float | int, *, text_align: ft.TextAlign) -> ft.Text:
    return ft.Text(
        text,
        size=13,
        color=TEXT_SOFT,
        width=width,
        text_align=text_align,
        max_lines=2,
    )


def _debt_outline_button(text: str, on_click, *, color: str) -> ft.OutlinedButton:
    return ft.OutlinedButton(
        text,
        on_click=on_click,
        height=_DEBT_ROW_MATCH_HEIGHT,
        style=ft.ButtonStyle(
            color=color,
            bgcolor=ft.Colors.TRANSPARENT,
            side=ft.BorderSide(1, GREEN_DARK),
            shape=ft.RoundedRectangleBorder(radius=6),
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            text_style=ft.TextStyle(size=_DEBT_ROW_TEXT_SIZE),
        ),
    )


def build_dashboard_view(
    content_width: float,
    username: str,
    mobile: bool,
    debt_total_field: ft.TextField,
    debt_editing: bool,
    on_edit_debt,
    on_save_debt,
    on_cancel_debt,
    interest_rate_field: ft.TextField,
    interest_term_dropdown: ft.Dropdown,
    installment_count_field: ft.TextField,
    first_due_date_field: ft.TextField,
    status_message: str,
    status_is_error: bool,
    on_calculate,
    on_open_debts_crud,
    on_logout,
) -> ft.Control:
    if mobile:
        card_pad = 12.0 if content_width < 400 else 16.0
    else:
        card_pad = 20.0
    row_width = content_width - 2 * card_pad
    narrow = row_width < 360
    gap = 12
    fit_width = max(row_width - 2, 120)
    right_width = int((fit_width - gap) * 0.38)
    left_width = (fit_width - gap) - right_width

    debt_total_field.read_only = not debt_editing
    if mobile:
        debt_total_field.width = row_width
    else:
        debt_total_field.width = None
    # ไม่ใช้ label ลอย — ใช้ข้อความด้านบนแทน จึงบังคับความสูงเท่าปุ่มได้ตรงกรอบ
    debt_total_field.label = ""
    debt_total_field.hint_text = ""
    debt_total_field.suffix = "บาท"
    debt_total_field.suffix_style = ft.TextStyle(color=TEXT_SOFT, size=_DEBT_ROW_TEXT_SIZE)
    debt_total_field.dense = False
    debt_total_field.height = _DEBT_ROW_MATCH_HEIGHT
    debt_total_field.border_radius = 6

    _input_ts = ft.TextStyle(color=TEXT_LIGHT, size=_DEBT_ROW_TEXT_SIZE)

    for control in [debt_total_field, interest_rate_field, installment_count_field, first_due_date_field]:
        control.border_color = GREEN_DARK
        control.color = TEXT_LIGHT
        control.focused_border_color = GREEN
        control.text_style = _input_ts
        control.bgcolor = CARD_DARK
        control.fill_color = CARD_DARK
        control.multiline = False
        control.min_lines = 1
        control.max_lines = 1

    interest_rate_field.label = ""
    interest_term_dropdown.label = ""
    interest_rate_field.hint_text = ""
    interest_rate_field.suffix = "%"
    interest_rate_field.suffix_style = ft.TextStyle(color=TEXT_SOFT, size=_DEBT_ROW_TEXT_SIZE)
    installment_count_field.label = ""
    first_due_date_field.label = ""
    installment_count_field.hint_text = ""
    installment_count_field.suffix = "งวด"
    installment_count_field.suffix_style = ft.TextStyle(color=TEXT_SOFT, size=_DEBT_ROW_TEXT_SIZE)
    first_due_date_field.hint_text = "แตะเลือกวันที่" if narrow else "แตะเพื่อเลือกจากปฏิทิน"

    if mobile:
        interest_rate_field.width = row_width
        interest_term_dropdown.width = row_width
        installment_count_field.width = row_width
        first_due_date_field.width = row_width
    else:
        interest_rate_field.width = left_width
        interest_term_dropdown.width = right_width
        installment_count_field.width = left_width
        first_due_date_field.width = right_width

    installment_count_field.height = _DEBT_ROW_MATCH_HEIGHT
    first_due_date_field.height = _DEBT_ROW_MATCH_HEIGHT
    installment_count_field.border_radius = 6
    first_due_date_field.border_radius = 6
    installment_count_field.dense = False
    first_due_date_field.dense = False

    interest_term_dropdown.height = _DEBT_ROW_MATCH_HEIGHT
    interest_term_dropdown.border_color = GREEN_DARK
    interest_term_dropdown.color = TEXT_LIGHT
    interest_term_dropdown.focused_border_color = GREEN
    interest_term_dropdown.bgcolor = CARD_DARK

    if debt_editing:
        debt_buttons = ft.Row(
            [
                _debt_outline_button("บันทึก", on_save_debt, color=TEXT_LIGHT),
                _debt_outline_button("ยกเลิก", on_cancel_debt, color=TEXT_SOFT),
            ],
            spacing=8,
        )
    else:
        debt_buttons = _debt_outline_button("แก้ไข", on_edit_debt, color=TEXT_SOFT)

    # มือถือ: อย่าใช้ Row+wrap+expand รอบ TextField — บนเว็บมักยืดช่องกรอกเป็นพื้นขาวยาว
    if mobile:
        debt_field_row = ft.Column(
            [
                debt_total_field,
                ft.Row(
                    [debt_buttons],
                    alignment=ft.MainAxisAlignment.CENTER,
                    width=row_width,
                ),
            ],
            spacing=8,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            width=row_width,
        )
    else:
        debt_field_row = ft.Row(
            [
                ft.Container(content=debt_total_field, expand=True),
                debt_buttons,
            ],
            width=row_width,
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    debt_row = ft.Column(
        [
            ft.Text(
                "ยอดหนี้",
                size=13,
                color=TEXT_SOFT,
                width=row_width,
                text_align=ft.TextAlign.CENTER,
                max_lines=2,
            ),
            debt_field_row,
        ],
        width=row_width,
        spacing=6,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    _cap_m = ft.TextAlign.CENTER
    _cap_d = ft.TextAlign.START
    if mobile:
        interest_row = ft.Container(
            width=row_width,
            content=ft.Column(
                [
                    ft.Column(
                        [
                            _input_caption("อัตรา %", row_width, text_align=_cap_m),
                            interest_rate_field,
                        ],
                        spacing=6,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        width=row_width,
                    ),
                    ft.Column(
                        [
                            _input_caption("ผ่อนทุก", row_width, text_align=_cap_m),
                            interest_term_dropdown,
                        ],
                        spacing=6,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        width=row_width,
                    ),
                ],
                spacing=gap,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )
        schedule_row = ft.Container(
            width=row_width,
            content=ft.Column(
                [
                    ft.Column(
                        [
                            _input_caption("จำนวนงวด", row_width, text_align=_cap_m),
                            installment_count_field,
                        ],
                        spacing=6,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        width=row_width,
                    ),
                    ft.Column(
                        [
                            _input_caption("งวดแรกครบกำหนด", row_width, text_align=_cap_m),
                            first_due_date_field,
                        ],
                        spacing=6,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        width=row_width,
                    ),
                ],
                spacing=gap,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )
    else:
        interest_row = ft.Container(
            width=row_width,
            content=ft.Row(
                [
                    ft.Column(
                        [
                            _input_caption("อัตรา %", left_width, text_align=_cap_d),
                            interest_rate_field,
                        ],
                        spacing=6,
                        horizontal_alignment=ft.CrossAxisAlignment.START,
                        width=left_width,
                    ),
                    ft.Column(
                        [
                            _input_caption("ผ่อนทุก", right_width, text_align=_cap_d),
                            interest_term_dropdown,
                        ],
                        spacing=6,
                        horizontal_alignment=ft.CrossAxisAlignment.START,
                        width=right_width,
                    ),
                ],
                spacing=gap,
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
        )
        schedule_row = ft.Container(
            width=row_width,
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    _input_caption("จำนวนงวด", left_width, text_align=_cap_d),
                                    installment_count_field,
                                ],
                                spacing=6,
                                horizontal_alignment=ft.CrossAxisAlignment.START,
                                width=left_width,
                            ),
                            ft.Column(
                                [
                                    _input_caption("งวดแรกครบกำหนด", right_width, text_align=_cap_d),
                                    first_due_date_field,
                                ],
                                spacing=6,
                                horizontal_alignment=ft.CrossAxisAlignment.START,
                                width=right_width,
                            ),
                        ],
                        spacing=gap,
                        alignment=ft.MainAxisAlignment.CENTER,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                        width=row_width,
                    ),
                ],
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
        )

    _btn_pad_v = 12 if narrow else 14
    _calc_btn_style = ft.ButtonStyle(
        text_style=ft.TextStyle(size=_DEBT_ROW_TEXT_SIZE),
        shape=ft.RoundedRectangleBorder(radius=8),
        padding=ft.padding.symmetric(horizontal=12 if narrow else 16, vertical=_btn_pad_v),
    )
    _debts_btn_style = ft.ButtonStyle(
        color=TEXT_LIGHT,
        side=ft.BorderSide(1, GREEN_DARK),
        shape=ft.RoundedRectangleBorder(radius=8),
        padding=ft.padding.symmetric(horizontal=10 if narrow else 12, vertical=_btn_pad_v),
        text_style=ft.TextStyle(size=_DEBT_ROW_TEXT_SIZE),
    )
    _logout_bg = "#9B2C2C"
    # มือถือ: ห้าม expand+wrap กับปุ่ม — มักยืดแนวตั้งเหมือนช่องกรอก
    if mobile:
        main_action_top = ft.Column(
            [
                ft.ElevatedButton(
                    "คำนวณ",
                    width=row_width,
                    bgcolor=GREEN_DARK,
                    color=TEXT_LIGHT,
                    on_click=on_calculate,
                    style=_calc_btn_style,
                ),
                ft.OutlinedButton(
                    "รายการหนี้",
                    width=row_width,
                    on_click=on_open_debts_crud,
                    style=_debts_btn_style,
                ),
            ],
            spacing=10,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            width=row_width,
        )
        logout_btn = ft.ElevatedButton(
            "ออกจากระบบ",
            width=row_width,
            bgcolor=_logout_bg,
            color=TEXT_LIGHT,
            on_click=on_logout,
            style=_calc_btn_style,
            margin=ft.margin.only(bottom=6),
        )
        main_action_row = ft.Column(
            [main_action_top, logout_btn],
            spacing=26,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            width=row_width,
        )
    else:
        main_action_top = ft.Row(
            [
                ft.ElevatedButton(
                    "คำนวณ",
                    expand=True,
                    bgcolor=GREEN_DARK,
                    color=TEXT_LIGHT,
                    on_click=on_calculate,
                    style=_calc_btn_style,
                ),
                ft.OutlinedButton(
                    "รายการหนี้",
                    expand=True,
                    on_click=on_open_debts_crud,
                    style=_debts_btn_style,
                ),
            ],
            width=row_width,
            spacing=10,
        )
        # ความกว้างเท่าปุ่มหนึ่งปุ่มในแถวบน (แบ่งครึ่งลบระยะห่าง)
        _logout_w = max(120.0, (row_width - 10) / 2)
        logout_btn = ft.ElevatedButton(
            "ออกจากระบบ",
            width=_logout_w,
            bgcolor=_logout_bg,
            color=TEXT_LIGHT,
            on_click=on_logout,
            style=_calc_btn_style,
            margin=ft.margin.only(bottom=6),
        )
        main_action_row = ft.Column(
            [
                main_action_top,
                ft.Row(
                    [logout_btn],
                    width=row_width,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
            ],
            spacing=26,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            width=row_width,
        )

    _title_size = 20 if narrow else 22

    return wrapped_card(
        ft.Column(
            [
                ft.Text(
                    "คำนวณหนี้",
                    size=_title_size,
                    weight=ft.FontWeight.BOLD,
                    color=GREEN,
                    text_align=ft.TextAlign.CENTER,
                    width=row_width,
                    max_lines=2,
                ),
                ft.Text(
                    f"สวัสดี {username}",
                    size=12,
                    color=TEXT_SOFT,
                    text_align=ft.TextAlign.CENTER,
                    width=row_width,
                    max_lines=2,
                    overflow=ft.TextOverflow.ELLIPSIS,
                ),
                debt_row,
                interest_row,
                schedule_row,
                main_action_row,
                status_text(status_message, status_is_error, width=row_width),
            ],
            spacing=10,
            tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.START,
        ),
        width=content_width,
        card_padding=card_pad,
    )
