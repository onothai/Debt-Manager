from __future__ import annotations

from decimal import Decimal

import flet as ft

from ui.loan_math import ScheduleSummary
from ui.theme import GREEN, GREEN_DARK, TEXT_LIGHT, TEXT_SOFT, format_money_decimal_display, wrapped_card


def term_th(term: str) -> str:
    return {"week": "สัปดาห์", "month": "เดือน", "year": "ปี"}.get(term, term)


def _money(d: Decimal) -> str:
    return format_money_decimal_display(d)


def build_result_view(
    content_width: float,
    mobile: bool,
    debt_total: str,
    interest_rate: str,
    interest_term: str,
    installment_count: str,
    first_due_label: str,
    rows: list[dict],
    summary: ScheduleSummary,
    on_back,
    *,
    interest_rate_basis: str | None = None,
    schedule_intro: str | None = None,
    back_button_text: str | None = None,
) -> ft.Control:
    row_width = content_width - 40
    # มือถือ: เว้นน้อยลงแต่ยังกว้างกว่าจอเล็กน้อย กันคอลัมน์ชิดขอบ
    _table_h_margin = 12 if mobile else 10
    _col_space = 10
    _scroll_end_pad = 20 if mobile else 12
    _table_box_pad = ft.padding.symmetric(horizontal=6, vertical=4) if mobile else None
    _data_table_width = row_width
    if mobile:
        _data_table_width = float(max(560, int(row_width) + 160))
    basis = interest_rate_basis or interest_term
    pay_label = term_th(interest_term)
    basis_label = term_th(basis)
    rate_line = f"อัตรา {interest_rate}% ต่อ{basis_label} · ผ่อนทุก{pay_label}"
    intro_default = "สรุปผลการคำนวณ (ดอกเบี้ยแบบลดต้นลดดอก — ยอดผ่อนเท่ากันทุกงวด)"
    intro_text = schedule_intro if schedule_intro is not None else intro_default
    back_label = back_button_text or "กลับไปหน้าคำนวณ"

    summary_lines = [
        ft.Text(
            intro_text,
            size=13,
            color=TEXT_SOFT,
            text_align=ft.TextAlign.CENTER,
            width=row_width,
        ),
        ft.Divider(color=GREEN_DARK, height=16),
        ft.Text(f"ยอดเงินต้น: {_money(Decimal(debt_total))} บาท", color=TEXT_LIGHT, width=row_width),
        ft.Text(
            rate_line,
            color=TEXT_LIGHT,
            width=row_width,
        ),
        ft.Text(f"จำนวนงวด: {installment_count} งวด", color=TEXT_LIGHT, width=row_width),
        ft.Text(f"วันครบกำหนดงวดแรก: {first_due_label}", color=TEXT_LIGHT, width=row_width),
        ft.Text(
            f"ยอดผ่อนต่องวด (โดยประมาณ): {_money(summary.payment_each)} บาท",
            color=GREEN,
            weight=ft.FontWeight.W_500,
            width=row_width,
        ),
        ft.Text(
            f"ดอกเบี้ยรวม: {_money(summary.total_interest)} บาท",
            color=TEXT_LIGHT,
            width=row_width,
        ),
        ft.Text(
            f"ยอดชำระรวม: {_money(summary.total_payment)} บาท",
            color=TEXT_LIGHT,
            width=row_width,
        ),
        ft.Text(
            f"วันจบหนี้ (งวดสุดท้าย): {summary.payoff_date.isoformat()}",
            color=GREEN,
            weight=ft.FontWeight.W_600,
            width=row_width,
        ),
        ft.Text(
            "งวดสุดท้ายอาจมียอดผ่อนแตกต่างเล็กน้อยจากการปัดเศษทศนิยม",
            size=12,
            color=TEXT_SOFT,
            width=row_width,
        ),
    ]

    table_header = ft.DataTable(
        width=_data_table_width,
        heading_row_height=44,
        data_row_min_height=40,
        column_spacing=_col_space,
        horizontal_margin=_table_h_margin,
        columns=[
            ft.DataColumn(ft.Text("งวด", color=TEXT_SOFT, size=12)),
            ft.DataColumn(ft.Text("ครบกำหนด", color=TEXT_SOFT, size=12)),
            ft.DataColumn(ft.Text("เงินต้น", color=TEXT_SOFT, size=12)),
            ft.DataColumn(ft.Text("ดอกเบี้ย", color=TEXT_SOFT, size=12)),
            ft.DataColumn(ft.Text("รวมชำระ", color=TEXT_SOFT, size=12)),
            ft.DataColumn(ft.Text("คงเหลือ", color=TEXT_SOFT, size=12)),
        ],
        rows=[
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(str(r["no"]), color=TEXT_LIGHT, size=12)),
                    ft.DataCell(ft.Text(r["due"].isoformat(), color=TEXT_LIGHT, size=11)),
                    ft.DataCell(ft.Text(_money(r["principal"]), color=TEXT_LIGHT, size=12)),
                    ft.DataCell(ft.Text(_money(r["interest"]), color=TEXT_LIGHT, size=12)),
                    ft.DataCell(ft.Text(_money(r["total"]), color=TEXT_LIGHT, size=12)),
                    ft.DataCell(ft.Text(_money(r["balance"]), color=TEXT_LIGHT, size=12)),
                ]
            )
            for r in rows
        ],
    )

    table_wrap = ft.Container(
        content=ft.Column(
            [
                ft.Text(
                    "ตารางผ่อนชำระ",
                    size=16,
                    weight=ft.FontWeight.W_500,
                    color=GREEN,
                    width=row_width,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Container(
                    width=row_width,
                    padding=_table_box_pad,
                    content=ft.Row(
                        [
                            ft.Container(width=_scroll_end_pad),
                            table_header,
                            ft.Container(width=_scroll_end_pad),
                        ],
                        scroll=ft.ScrollMode.AUTO,
                        spacing=0,
                    ),
                    border=ft.border.all(1, GREEN_DARK),
                    border_radius=8,
                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                ),
            ],
            spacing=8,
            tight=True,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        width=row_width,
    )

    return wrapped_card(
        ft.Column(
            [
                ft.Text("ผลการคำนวณหนี้", size=24, weight=ft.FontWeight.BOLD, color=GREEN),
                *summary_lines,
                table_wrap,
                ft.ElevatedButton(
                    back_label,
                    width=row_width,
                    bgcolor=GREEN_DARK,
                    color=TEXT_LIGHT,
                    on_click=on_back,
                ),
            ],
            tight=True,
            spacing=8,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
        ),
        width=content_width,
    )
