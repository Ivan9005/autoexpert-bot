from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, Text, DateTime
from datetime import datetime


class Base(DeclarativeBase):
    pass


class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    client_fio: Mapped[str] = mapped_column(String)
    reg_address: Mapped[str] = mapped_column(Text)
    phone: Mapped[str] = mapped_column(String)

    passport: Mapped[str] = mapped_column(String)
    passport_issued_by: Mapped[str] = mapped_column(Text)
    passport_issued_date: Mapped[str] = mapped_column(String)

    auto_model: Mapped[str] = mapped_column(String)
    auto_year: Mapped[str] = mapped_column(String)
    vin: Mapped[str] = mapped_column(String)
    gos_number: Mapped[str] = mapped_column(String)
    sts_number: Mapped[str] = mapped_column(String)

    city: Mapped[str] = mapped_column(String)
    contract_date: Mapped[str] = mapped_column(String)

    file_path: Mapped[str] = mapped_column(Text)

    status: Mapped[str] = mapped_column(String, default="new")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)