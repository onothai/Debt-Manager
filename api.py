from __future__ import annotations

"""
Debt Manager API — FastAPI + Pydantic validation + MariaDB (SQLAlchemy ORM).

โครงสร้างข้อมูลหลัก (อย่างน้อย 2 ตารางที่มีความสัมพันธ์):
- user (ผู้ใช้)
- debt (หนี้แต่ละรายการ, FK → user.user_id)
- installment (งวดผ่อน, FK → debt.debt_id) — สร้างอัตโนมัติเมื่อ POST /debts

CRUD: /users และ /debts รองรับ Create, Read, Update, Delete ครบ
"""

import os

import app_config  # noqa: F401 — โหลด .env ก่อนอ่าน DB_* / UVICORN_*

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Generator, Literal, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Date, Enum as SAEnum, ForeignKey, Numeric, String, create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker

from ui.loan_math import add_n_periods, rate_percent_to_decimal_per_payment

# PyMySQL ไม่รองรับ auth_gssapi_client — อย่าใช้ DB_USER=root ถ้า root บน MariaDB ใช้ปลั๊กอินนั้น (จะ error 2059)
# บนเซิร์ฟเวอร์ DB: ต้องมี 'api_user'@'%' และรหัสตรงกับ $env:DB_PASSWORD
# ถ้ามีแถว api_user@% แล้วแต่ยัง 1045: มักเป็นรหัสผ่านไม่ตรง หรือปลั๊กอินไม่ใช่ mysql_native_password
# ตรวจสอบ:
#   SELECT user, host, plugin FROM mysql.user WHERE user = 'api_user';
# บังคับรหัส + native password (แก้ทั้งรหัสผิดและปลั๊กอิน ed25519 บางกรณี):
#   ALTER USER 'api_user'@'%' IDENTIFIED VIA mysql_native_password USING PASSWORD('P@ssw0rd');
#   FLUSH PRIVILEGES;
# ทดสอบจากเครื่องรัน API: mysql -u api_user -p -h 192.168.137.50 bidkom
# ค่า DB ใส่ในไฟล์ .env (ดู .env.example) จะไม่ต้องตั้ง $env: ทุกครั้งหลังรีบูตเครื่อง
DB_HOST = os.getenv("DB_HOST", "192.168.137.50")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
# ค่าเริ่มต้นเป็น api_user — อย่าใช้ root เป็นค่าเริ่มต้นถ้า MariaDB ใช้ auth_gssapi กับ root (PyMySQL จะ error 2059)
DB_USER = os.getenv("DB_USER", "api_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "P@ssw0rd")
DB_NAME = os.getenv("DB_NAME", "bidkom")

DB_URL = URL.create(
    drivername="mysql+pymysql",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
)

engine = create_engine(DB_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# ถ้า create_db() ตอน startup ล้ม จะเก็บข้อความไว้ — ยังเปิด /docs ได้ แต่ endpoint ที่ใช้ DB จะ error
db_startup_error: str | None = None


class Base(DeclarativeBase):
    pass


class DebtStatus(str, Enum):
    active = "active"
    paid = "paid"


class InterestType(str, Enum):
    flat = "flat"
    reducing = "reducing"


class InstallmentStatus(str, Enum):
    paid = "paid"
    unpaid = "unpaid"


class User(Base):
    __tablename__ = "user"

    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100))
    password: Mapped[str] = mapped_column(String(100))
    debt_total: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    debts: Mapped[list["Debt"]] = relationship("Debt", back_populates="user", cascade="all, delete-orphan")


class Debt(Base):
    __tablename__ = "debt"

    debt_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.user_id", ondelete="CASCADE"), index=True)
    debt_name: Mapped[str] = mapped_column(String(100))
    principal: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    interest_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2))
    # ฐานของตัวเลข interest_rate: week / month / year
    interest_rate_basis: Mapped[str] = mapped_column(String(16), default="year")
    # ความถี่งวดจ่าย: week / month / year (กำหนดระยะห่างครบกำหนด + อัตราต่องวด)
    payment_period: Mapped[str] = mapped_column(String(16), default="month")
    interest_type: Mapped[InterestType] = mapped_column("interest_type", SAEnum(InterestType), default=InterestType.flat)
    total_installments: Mapped[int] = mapped_column("total_installments")
    start_date: Mapped[date] = mapped_column(Date())
    end_date: Mapped[date] = mapped_column(Date())
    status: Mapped[DebtStatus] = mapped_column(SAEnum(DebtStatus), default=DebtStatus.active)

    user: Mapped[User] = relationship("User", back_populates="debts")
    installments: Mapped[list["Installment"]] = relationship(
        "Installment",
        back_populates="debt",
        cascade="all, delete-orphan",
        order_by="Installment.installment_no",
    )


class Installment(Base):
    __tablename__ = "installment"

    installment_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    debt_id: Mapped[int] = mapped_column(ForeignKey("debt.debt_id", ondelete="CASCADE"), index=True)
    installment_no: Mapped[int] = mapped_column()
    due_date: Mapped[date] = mapped_column(Date())
    principal_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    interest_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    remaining_balance: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    installment_status: Mapped[InstallmentStatus] = mapped_column(
        "installment_status",
        SAEnum(InstallmentStatus),
        default=InstallmentStatus.unpaid,
    )

    debt: Mapped[Debt] = relationship("Debt", back_populates="installments")


def create_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    if db_startup_error:
        raise HTTPException(
            status_code=503,
            detail="MariaDB ยังเชื่อมไม่ได้ (startup): " + db_startup_error[:800],
        )
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def dec2(value: Decimal | float | int) -> Decimal:
    return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def build_installments(
    principal: Decimal,
    interest_rate: Decimal,
    interest_type: InterestType,
    total_installments: int,
    start_date: date,
    *,
    interest_rate_basis: str = "year",
    payment_period: str = "month",
) -> list[dict]:
    if total_installments <= 0:
        raise HTTPException(status_code=400, detail="total_installments must be greater than 0")

    rows: list[dict] = []
    principal = dec2(principal)
    basis = interest_rate_basis if interest_rate_basis in ("week", "month", "year") else "year"
    pp = payment_period if payment_period in ("week", "month", "year") else "month"
    r = rate_percent_to_decimal_per_payment(dec2(interest_rate), basis, pp)
    principal_per_installment = dec2(principal / Decimal(total_installments))
    remain = principal

    for i in range(1, total_installments + 1):
        due = add_n_periods(start_date, pp, i)
        if interest_type == InterestType.flat:
            interest_amount = dec2(principal * r)
        else:
            interest_amount = dec2(remain * r)

        current_principal = principal_per_installment
        if i == total_installments:
            current_principal = dec2(remain)

        remain_after = dec2(remain - current_principal)
        total_amount = dec2(current_principal + interest_amount)

        rows.append(
            {
                "installment_no": i,
                "due_date": due,
                "principal_amount": current_principal,
                "interest_amount": interest_amount,
                "total_amount": total_amount,
                "remaining_balance": remain_after,
                "installment_status": InstallmentStatus.unpaid,
            }
        )
        remain = remain_after

    return rows


def update_debt_status_from_installments(debt: Debt) -> None:
    if not debt.installments:
        debt.status = DebtStatus.active
        return
    paid_all = all(i.installment_status == InstallmentStatus.paid for i in debt.installments)
    debt.status = DebtStatus.paid if paid_all else DebtStatus.active
    debt.end_date = debt.installments[-1].due_date


class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=100)
    debt_total: Decimal = Field(default=Decimal("0"), ge=0)


class UserUpdate(BaseModel):
    username: Optional[str] = Field(default=None, min_length=1, max_length=100)
    password: Optional[str] = Field(default=None, min_length=1, max_length=100)
    debt_total: Optional[Decimal] = Field(default=None, ge=0)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: int
    username: str
    password: str
    debt_total: Decimal


class DebtCreate(BaseModel):
    user_id: int
    debt_name: str = Field(min_length=1, max_length=100)
    principal: Decimal = Field(gt=0)
    interest_rate: Decimal = Field(ge=0)
    interest_rate_basis: Literal["week", "month", "year"] = "year"
    payment_period: Literal["week", "month", "year"] = "month"
    interest_type: InterestType
    total_installments: int = Field(gt=0, le=600)
    start_date: date


class DebtUpdate(BaseModel):
    debt_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    principal: Optional[Decimal] = Field(default=None, gt=0)
    interest_rate: Optional[Decimal] = Field(default=None, ge=0)
    interest_rate_basis: Optional[Literal["week", "month", "year"]] = None
    payment_period: Optional[Literal["week", "month", "year"]] = None
    interest_type: Optional[InterestType] = None
    total_installments: Optional[int] = Field(default=None, gt=0, le=600)
    start_date: Optional[date] = None
    status: Optional[DebtStatus] = None


class DebtDeleteByIdPayload(BaseModel):
    """ลบตาม debt_id — ใช้กับ POST /debts/remove (เลี่ยงพร็อกซีที่บล็อก DELETE หรือ path แปลกๆ)"""

    debt_id: int = Field(gt=0)


class DebtOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    debt_id: int
    user_id: int
    debt_name: str
    principal: Decimal
    interest_rate: Decimal
    interest_rate_basis: str
    payment_period: str
    interest_type: InterestType
    total_installments: int
    start_date: date
    end_date: date
    status: DebtStatus


class InstallmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    installment_id: int
    debt_id: int
    installment_no: int
    due_date: date
    principal_amount: Decimal
    interest_amount: Decimal
    total_amount: Decimal
    remaining_balance: Decimal
    installment_status: InstallmentStatus


class InstallmentUpdate(BaseModel):
    installment_status: InstallmentStatus


app = FastAPI(
    title="Debt Manager API",
    version="1.0.0",
    servers=[
        {
            "url": app_config.client_api_base_url(),
            "description": "จาก .env (API_BASE_URL หรือ UVICORN_HOST + UVICORN_PORT)",
        }
    ],
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _mysql_errno(exc: Exception) -> int | None:
    orig = getattr(exc, "orig", None)
    if orig is not None and getattr(orig, "args", None):
        try:
            return int(orig.args[0])
        except (TypeError, ValueError, IndexError):
            pass
    return None


def _is_auth_plugin_gssapi_error(exc: Exception) -> bool:
    if _mysql_errno(exc) == 2059:
        return True
    msg = str(exc).lower()
    return "auth_gssapi" in msg


def _is_access_denied_error(exc: Exception) -> bool:
    return _mysql_errno(exc) == 1045


def _ensure_debt_columns() -> None:
    """
    ตาราง debt เก่าอาจไม่มี interest_rate_basis / payment_period — ORM จะ SELECT คอลัมน์เหล่านี้
    แล้ว MariaDB error → FastAPI ตอบ 500 (เช่น GET /debts). พยายาม ALTER เพิ่มคอลัมน์ตอน startup;
    ถ้ามีอยู่แล้ว (errno 1060) ให้ข้าม
    """
    statements = [
        "ALTER TABLE debt ADD COLUMN interest_rate_basis VARCHAR(16) NOT NULL DEFAULT 'year'",
        "ALTER TABLE debt ADD COLUMN payment_period VARCHAR(16) NOT NULL DEFAULT 'month'",
    ]
    with engine.begin() as conn:
        for stmt in statements:
            try:
                conn.execute(text(stmt))
            except Exception as e:
                if _mysql_errno(e) == 1060:
                    continue
                if "duplicate column" in str(e).lower():
                    continue
                raise


@app.on_event("startup")
def startup() -> None:
    global db_startup_error
    db_startup_error = None
    try:
        create_db()
    except OperationalError as e:
        db_startup_error = str(e)
        if _is_auth_plugin_gssapi_error(e):
            print(
                "[api] WARNING MariaDB (2059 auth_gssapi): ใช้ DB_USER=api_user + mysql_native_password — ดูคอมเมนต์ใน api.py"
            )
        elif _is_access_denied_error(e):
            print("[api] WARNING MariaDB (1045): รหัส/host ไม่ตรง — ตรวจ api_user@'%' และ DB_PASSWORD")
        else:
            print("[api] WARNING เชื่อม MariaDB ไม่ได้:", e)
    except Exception as e:
        db_startup_error = str(e)
        print("[api] WARNING create_db ล้ม:", e)
    if db_startup_error is None:
        try:
            _ensure_debt_columns()
        except Exception as e:
            print(
                "[api] WARNING เพิ่มคอลัมน์ debt (interest_rate_basis / payment_period) ไม่สำเร็จ — "
                "GET /debts อาจ 500 จนกว่าจะรัน ALTER เดียวกับใน _ensure_debt_columns() หรือให้ user DB สิทธิ์ ALTER:",
                e,
            )


@app.get("/")
def root() -> dict:
    return {"message": "Debt Manager API is running"}


@app.get("/health")
def health():
    base = {
        "api": "ok",
        "db_host": DB_HOST,
        "db_port": DB_PORT,
        "db_name": DB_NAME,
    }
    if db_startup_error:
        return JSONResponse(
            status_code=503,
            content={
                **base,
                "database": "startup_failed",
                "detail": db_startup_error,
            },
        )
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {**base, "database": "ok"}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={**base, "database": "ping_failed", "detail": str(e)},
        )


@app.post("/users", response_model=UserOut)
def create_user(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    user = User(
        username=payload.username,
        password=payload.password,
        debt_total=dec2(payload.debt_total),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)) -> list[User]:
    return db.query(User).order_by(User.user_id.desc()).all()


@app.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.put("/users/{user_id}", response_model=UserOut)
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for key, value in payload.model_dump(exclude_none=True).items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user


@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)) -> dict:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # ลบลูกก่อนแม่ — MariaDB FK ไม่ยอมลบ user ถ้ายังมี debt / installment อ้างอิง
    debts = db.query(Debt).filter(Debt.user_id == user_id).all()
    for debt in debts:
        db.query(Installment).filter(Installment.debt_id == debt.debt_id).delete(synchronize_session=False)
        db.delete(debt)
    db.flush()
    db.delete(user)
    db.commit()
    return {"message": "User deleted"}


@app.post("/debts", response_model=DebtOut)
def create_debt(payload: DebtCreate, db: Session = Depends(get_db)) -> Debt:
    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    schedule = build_installments(
        principal=payload.principal,
        interest_rate=payload.interest_rate,
        interest_type=payload.interest_type,
        total_installments=payload.total_installments,
        start_date=payload.start_date,
        interest_rate_basis=payload.interest_rate_basis,
        payment_period=payload.payment_period,
    )

    debt = Debt(
        user_id=payload.user_id,
        debt_name=payload.debt_name,
        principal=dec2(payload.principal),
        interest_rate=dec2(payload.interest_rate),
        interest_rate_basis=payload.interest_rate_basis,
        payment_period=payload.payment_period,
        interest_type=payload.interest_type,
        total_installments=payload.total_installments,
        start_date=payload.start_date,
        end_date=schedule[-1]["due_date"],
        status=DebtStatus.active,
    )
    db.add(debt)
    db.flush()

    for row in schedule:
        db.add(Installment(debt_id=debt.debt_id, **row))

    db.commit()
    db.refresh(debt)
    return debt


@app.get("/debts", response_model=list[DebtOut])
def list_debts(
    user_id: Optional[int] = Query(default=None),
    status: Optional[DebtStatus] = Query(default=None),
    db: Session = Depends(get_db),
) -> list[Debt]:
    query = db.query(Debt)
    if user_id is not None:
        query = query.filter(Debt.user_id == user_id)
    if status is not None:
        query = query.filter(Debt.status == status)
    return query.order_by(Debt.debt_id.desc()).all()


@app.get("/debts/{debt_id}", response_model=DebtOut)
def get_debt(debt_id: int, db: Session = Depends(get_db)) -> Debt:
    debt = db.get(Debt, debt_id)
    if not debt:
        raise HTTPException(status_code=404, detail="Debt not found")
    return debt


@app.put("/debts/{debt_id}", response_model=DebtOut)
def update_debt(debt_id: int, payload: DebtUpdate, db: Session = Depends(get_db)) -> Debt:
    debt = db.get(Debt, debt_id)
    if not debt:
        raise HTTPException(status_code=404, detail="Debt not found")

    data = payload.model_dump(exclude_none=True)
    recalculate_keys = {
        "principal",
        "interest_rate",
        "interest_rate_basis",
        "payment_period",
        "interest_type",
        "total_installments",
        "start_date",
    }

    for key, value in data.items():
        setattr(debt, key, value)

    if recalculate_keys.intersection(data.keys()):
        db.query(Installment).filter(Installment.debt_id == debt.debt_id).delete()
        schedule = build_installments(
            principal=debt.principal,
            interest_rate=debt.interest_rate,
            interest_type=debt.interest_type,
            total_installments=debt.total_installments,
            start_date=debt.start_date,
            interest_rate_basis=debt.interest_rate_basis or "year",
            payment_period=getattr(debt, "payment_period", None) or "month",
        )
        debt.end_date = schedule[-1]["due_date"]
        for row in schedule:
            db.add(Installment(debt_id=debt.debt_id, **row))
        debt.status = DebtStatus.active
    else:
        update_debt_status_from_installments(debt)

    db.commit()
    db.refresh(debt)
    return debt


def _delete_debt_by_id(db: Session, debt_id: int) -> dict:
    """ลบด้วย bulk delete สองขั้น — ลดปัญหา session/relationship ของ ORM หลังลบ installment"""
    try:
        db.query(Installment).filter(Installment.debt_id == debt_id).delete(synchronize_session=False)
        n_debt = db.query(Debt).filter(Debt.debt_id == debt_id).delete(synchronize_session=False)
        if n_debt == 0:
            db.rollback()
            raise HTTPException(status_code=404, detail="Debt not found")
        db.commit()
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="MariaDB: " + str(e)[:800]) from e
    return {"message": "Debt deleted"}


@app.delete("/debts/{debt_id}")
def delete_debt(debt_id: int, db: Session = Depends(get_db)) -> dict:
    return _delete_debt_by_id(db, debt_id)


@app.post("/debts/{debt_id}/delete")
def delete_debt_post(debt_id: int, db: Session = Depends(get_db)) -> dict:
    """ลบเหมือน DELETE — ใช้ POST เลี่ยงพร็อกซี/ไฟร์วอลล์ที่บล็อกคำสั่ง DELETE แต่ยังยอม PUT/POST"""
    return _delete_debt_by_id(db, debt_id)


@app.post("/debts/remove")
def delete_debt_by_json(payload: DebtDeleteByIdPayload, db: Session = Depends(get_db)) -> dict:
    """ลบหนี้ตาม debt_id ใน JSON — คู่ขนานกับ DELETE / POST …/delete"""
    return _delete_debt_by_id(db, payload.debt_id)


@app.get("/debts/{debt_id}/installments", response_model=list[InstallmentOut])
def list_installments(debt_id: int, db: Session = Depends(get_db)) -> list[Installment]:
    debt = db.get(Debt, debt_id)
    if not debt:
        raise HTTPException(status_code=404, detail="Debt not found")
    return db.query(Installment).filter(Installment.debt_id == debt_id).order_by(Installment.installment_no).all()


@app.put("/installments/{installment_id}", response_model=InstallmentOut)
def update_installment(installment_id: int, payload: InstallmentUpdate, db: Session = Depends(get_db)) -> Installment:
    row = db.get(Installment, installment_id)
    if not row:
        raise HTTPException(status_code=404, detail="Installment not found")

    row.installment_status = payload.installment_status
    db.flush()

    debt = db.get(Debt, row.debt_id)
    if debt:
        update_debt_status_from_installments(debt)

    db.commit()
    db.refresh(row)
    return row

