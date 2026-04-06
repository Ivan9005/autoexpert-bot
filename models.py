from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer


class Base(DeclarativeBase):
    pass


class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    client_fio: Mapped[str] = mapped_column(String)
    phone: Mapped[str] = mapped_column(String)
    auto_model: Mapped[str] = mapped_column(String)
    vin: Mapped[str] = mapped_column(String)