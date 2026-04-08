from __future__ import annotations

import flet as ft

from ui.theme import GREEN, GREEN_DARK, TEXT_LIGHT, TEXT_SOFT, status_text, wrapped_card


def build_login_view(
    content_width: float,
    username_field: ft.TextField,
    password_field: ft.TextField,
    status_message: str,
    status_is_error: bool,
    on_login,
    on_go_signup,
) -> ft.Control:
    username_field.border_color = GREEN_DARK
    username_field.color = TEXT_LIGHT
    username_field.focused_border_color = GREEN
    _inner_w = content_width - 40
    username_field.width = _inner_w
    password_field.border_color = GREEN_DARK
    password_field.color = TEXT_LIGHT
    password_field.focused_border_color = GREEN
    password_field.width = _inner_w

    return wrapped_card(
        ft.Column(
            [
                ft.Text(
                    "Debt Manager",
                    size=30,
                    weight=ft.FontWeight.BOLD,
                    color=GREEN,
                    text_align=ft.TextAlign.CENTER,
                    width=_inner_w,
                    max_lines=2,
                ),
                ft.Text(
                    "ระบบจัดการหนี้ - Login",
                    size=14,
                    color=TEXT_SOFT,
                    text_align=ft.TextAlign.CENTER,
                    width=_inner_w,
                ),
                username_field,
                password_field,
                ft.ElevatedButton(
                    "เข้าสู่ระบบ",
                    width=_inner_w,
                    bgcolor=GREEN_DARK,
                    color=TEXT_LIGHT,
                    on_click=on_login,
                ),
                ft.TextButton("ยังไม่มีบัญชี? สมัครสมาชิก", on_click=on_go_signup),
                status_text(status_message, status_is_error, width=_inner_w),
            ],
            tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        width=content_width,
    )
