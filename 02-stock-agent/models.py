from datetime import date

from sqlalchemy import (
    Boolean,
    Date,
    Float,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class StockSnapshotORM(Base):
    __tablename__ = "stock_snapshots"

    __table_args__ = (
        UniqueConstraint(
            "stock_code",
            "snapshot_date",
            name="uq_stock_code_snapshot_date",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    stock_code: Mapped[str] = mapped_column(String(20))
    stock_name: Mapped[str] = mapped_column(String(100))

    close_price: Mapped[float] = mapped_column(Float)
    change_percent: Mapped[float] = mapped_column(Float)
    turnover_amount: Mapped[float] = mapped_column(Float)
    market_cap: Mapped[float] = mapped_column(Float)
    turnover_rate: Mapped[float] = mapped_column(Float)


    is_st: Mapped[bool] = mapped_column(Boolean)
    snapshot_date: Mapped[date] = mapped_column(Date)

    data_source: Mapped[str] = mapped_column(
        String(20),
        default="xueqiu",
    )