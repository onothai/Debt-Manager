"""คำนวณตารางผ่อนแบบลดต้นลดดอก (ยอดผ่อนเท่ากันทุกงวด) — ใช้ในแอปและ API (แปลงอัตราระหว่างฐานกับความถี่งวด)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

_Q = Decimal("0.01")


def _days_in_month(year: int, month: int) -> int:
    if month in (1, 3, 5, 7, 8, 10, 12):
        return 31
    if month in (4, 6, 9, 11):
        return 30
    if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0):
        return 29
    return 28


def add_months(d: date, months: int) -> date:
    """บวกเดือนแบบจับวันในเดือน (เช่น 31 ม.ค. +1 เดือน → 28/29 ก.พ.)."""
    total = (d.year * 12 + d.month - 1) + months
    y, m0 = divmod(total, 12)
    m = m0 + 1
    day = min(d.day, _days_in_month(y, m))
    return date(y, m, day)


def add_one_period(d: date, term: str) -> date:
    if term == "week":
        return d + timedelta(days=7)
    if term == "month":
        return add_months(d, 1)
    if term == "year":
        return add_months(d, 12)
    raise ValueError(f"unknown term: {term!r}")


def add_n_periods(d: date, term: str, n: int) -> date:
    out = d
    for _ in range(max(0, n)):
        out = add_one_period(out, term)
    return out


def _q(x: Decimal) -> Decimal:
    return x.quantize(_Q, ROUND_HALF_UP)


def _pmt(principal: Decimal, r: Decimal, n: int) -> Decimal:
    """ยอดผ่อนคงที่ต่องวด (r = อัตราต่อหนึ่งงวดเป็นเศษส่วน เช่น 0.01 = 1%)."""
    if n < 1:
        raise ValueError("จำนวนงวดต้องไม่น้อยกว่า 1")
    if principal <= 0:
        raise ValueError("เงินต้นต้องมากกว่า 0")
    if r == 0:
        return _q(principal / n)
    one = Decimal(1)
    denom = one - (one + r) ** (-n)
    if denom == 0:
        return _q(principal / n)
    return _q(principal * r / denom)


@dataclass(frozen=True)
class ScheduleSummary:
    payment_each: Decimal
    total_payment: Decimal
    total_interest: Decimal
    payoff_date: date


# จำนวนงวดต่อปี (โนมินัล) — ใช้แปลงอัตราระหว่างฐานอัตรากับความถี่งวดจ่าย
_PERIODS_PER_YEAR: dict[str, Decimal] = {
    "week": Decimal("52"),
    "month": Decimal("12"),
    "year": Decimal("1"),
}


def rate_percent_to_decimal_per_payment(
    rate_percent: Decimal,
    rate_basis: str,
    payment_period: str,
) -> Decimal:
    """
    แปลง % ที่ผู้ใช้กรอก (ตามฐาน rate_basis) เป็นอัตราเป็นทศนิยมต่องวดจ่ายหนึ่งครั้ง (payment_period).
    สมมติอัตราโนมินัล: ดอกต่อปี 7.5% + จ่ายรายเดือน → 0.075/12 ต่องวด
    """
    if rate_basis not in _PERIODS_PER_YEAR or payment_period not in _PERIODS_PER_YEAR:
        raise ValueError("หน่วยอัตราหรือความถี่งวดไม่ถูกต้อง")
    i = rate_percent / Decimal("100")
    nb = _PERIODS_PER_YEAR[rate_basis]
    np_ = _PERIODS_PER_YEAR[payment_period]
    return i * (nb / np_)


def compute_reducing_balance_schedule(
    principal: Decimal,
    rate_percent: Decimal,
    num_installments: int,
    first_due_date: date,
    payment_period: str,
    *,
    rate_basis: str | None = None,
) -> tuple[list[dict], ScheduleSummary]:
    """
    ดอกเบี้ยคิดจากยอดคงค้างงวดปัจจุบัน (ลดต้นลดดอก) ยอดผ่อนเท่ากันทุกงวด (ยกเว้นงวดสุดท้ายอาจสะสมจากการปัดเศษ).

    rate_percent: ตัวเลข % ที่กรอก ตามฐาน rate_basis (ถ้าไม่ส่ง rate_basis ใช้เท่ากับ payment_period แบบเดิม)
    payment_period: ความถี่งวดจ่าย — สัปดาห์ / เดือน / ปี
    """
    n = num_installments
    if n < 1:
        raise ValueError("กรุณากรอกจำนวนงวดอย่างน้อย 1")
    if principal <= 0:
        raise ValueError("ยอดหนี้ต้องมากกว่า 0")
    if rate_percent < 0:
        raise ValueError("อัตราดอกเบี้ยต้องไม่ติดลบ")

    basis = rate_basis if rate_basis is not None else payment_period
    r = rate_percent_to_decimal_per_payment(rate_percent, basis, payment_period)
    rows: list[dict] = []
    balance = principal

    if r == 0:
        pay = _q(principal / n)
        total_int = Decimal("0")
        total_pay = Decimal("0")
        for i in range(1, n + 1):
            due = add_n_periods(first_due_date, payment_period, i - 1)
            if i == n:
                prin = balance
            else:
                prin = pay
            int_amt = Decimal("0")
            tot = _q(prin + int_amt)
            balance = _q(balance - prin)
            total_pay += tot
            rows.append(
                {
                    "no": i,
                    "due": due,
                    "principal": prin,
                    "interest": int_amt,
                    "total": tot,
                    "balance": balance,
                }
            )
        payoff = rows[-1]["due"]
        return rows, ScheduleSummary(
            payment_each=pay if n > 1 else rows[0]["total"],
            total_payment=_q(total_pay),
            total_interest=_q(total_int),
            payoff_date=payoff,
        )

    payment = _pmt(principal, r, n)
    total_int = Decimal("0")
    total_pay = Decimal("0")

    for i in range(1, n + 1):
        due = add_n_periods(first_due_date, payment_period, i - 1)
        int_amt = _q(balance * r)
        if i < n:
            prin = _q(payment - int_amt)
            if prin > balance:
                prin = balance
            tot = _q(prin + int_amt)
        else:
            prin = balance
            tot = _q(prin + int_amt)
        balance = _q(balance - prin)
        total_int += int_amt
        total_pay += tot
        rows.append(
            {
                "no": i,
                "due": due,
                "principal": prin,
                "interest": int_amt,
                "total": tot,
                "balance": balance,
            }
        )

    payoff = rows[-1]["due"]
    return rows, ScheduleSummary(
        payment_each=payment,
        total_payment=_q(total_pay),
        total_interest=_q(total_int),
        payoff_date=payoff,
    )


def compute_installment_schedule_api_style(
    principal: Decimal,
    rate_percent: Decimal,
    num_installments: int,
    start_date: date,
    *,
    rate_basis: str = "year",
    payment_period: str = "month",
    flat_interest: bool,
) -> tuple[list[dict], ScheduleSummary]:
    """
    จำลอง build_installments ของ API — เงินต้นต่องวดเท่ากัน (ยกเว้นงวดสุดท้าย),
    ดอกแบบ flat คิดจากเงินต้นเต็ม แบบ reducing คิดจากยอดคงค้าง.
    งวดที่ i ครบกำหนด = บวก i รอบตาม payment_period (สัปดาห์ / เดือน / ปี) จาก start_date.
    """
    n = num_installments
    if n < 1:
        raise ValueError("กรุณากรอกจำนวนงวดอย่างน้อย 1")
    if principal <= 0:
        raise ValueError("ยอดหนี้ต้องมากกว่า 0")
    if rate_percent < 0:
        raise ValueError("อัตราดอกเบี้ยต้องไม่ติดลบ")

    basis = rate_basis if rate_basis in ("week", "month", "year") else "year"
    pp = payment_period if payment_period in ("week", "month", "year") else "month"
    r = rate_percent_to_decimal_per_payment(rate_percent, basis, pp)
    p0 = _q(principal)
    ppi = _q(p0 / Decimal(n))
    balance = p0
    rows: list[dict] = []
    total_int = Decimal("0")
    total_pay = Decimal("0")

    for i in range(1, n + 1):
        due = add_n_periods(start_date, pp, i)
        if flat_interest:
            int_amt = _q(p0 * r)
        else:
            int_amt = _q(balance * r)
        if i == n:
            prin = balance
        else:
            prin = ppi
            if prin > balance:
                prin = balance
        tot = _q(prin + int_amt)
        balance = _q(balance - prin)
        total_int += int_amt
        total_pay += tot
        rows.append(
            {
                "no": i,
                "due": due,
                "principal": prin,
                "interest": int_amt,
                "total": tot,
                "balance": balance,
            }
        )

    payoff = rows[-1]["due"]
    pay_each = rows[0]["total"] if rows else Decimal("0")
    return rows, ScheduleSummary(
        payment_each=pay_each,
        total_payment=_q(total_pay),
        total_interest=_q(total_int),
        payoff_date=payoff,
    )
