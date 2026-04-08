from __future__ import annotations

import flet as ft

from ui.theme import (
    SIGNUP_ACCENT,
    SIGNUP_ACCENT_DARK,
    SIGNUP_BORDER,
    SIGNUP_TEXT_LIGHT,
    SIGNUP_TEXT_SOFT,
    status_text_signup,
    wrapped_signup_card,
)


def build_signup_view(
    content_width: float,
    username_field: ft.TextField,
    password_field: ft.TextField,
    status_message: str,
    status_is_error: bool,
    on_signup,
    on_go_login,
) -> ft.Control:
    _inner_w = content_width - 40
    username_field.border_color = SIGNUP_BORDER
    username_field.color = SIGNUP_TEXT_LIGHT
    username_field.focused_border_color = SIGNUP_ACCENT
    username_field.width = _inner_w
    password_field.border_color = SIGNUP_BORDER
    password_field.color = SIGNUP_TEXT_LIGHT
    password_field.focused_border_color = SIGNUP_ACCENT
    password_field.width = _inner_w

    return wrapped_signup_card(
        ft.Column(
            [
                ft.Text(
                    "Debt Manager",
                    size=30,
                    weight=ft.FontWeight.BOLD,
                    color=SIGNUP_ACCENT,
                    text_align=ft.TextAlign.CENTER,
                    width=_inner_w,
                    max_lines=2,
                ),
                ft.Text(
                    "ระบบจัดการหนี้ - Signup",
                    size=14,
                    color=SIGNUP_TEXT_SOFT,
                    text_align=ft.TextAlign.CENTER,
                    width=_inner_w,
                ),
                username_field,
                password_field,
                ft.ElevatedButton(
                    "สมัครสมาชิก",
                    width=_inner_w,
                    bgcolor=SIGNUP_ACCENT_DARK,
                    color=SIGNUP_TEXT_LIGHT,
                    on_click=on_signup,
                ),
                ft.TextButton(
                    "มีบัญชีแล้ว? เข้าสู่ระบบ",
                    on_click=on_go_login,
                    style=ft.ButtonStyle(color=SIGNUP_TEXT_SOFT),
                ),
                status_text_signup(status_message, status_is_error, width=_inner_w),
            ],
            tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        width=content_width,
    )
