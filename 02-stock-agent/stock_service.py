from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models import StockSnapshotORM
from schemas import StockQuery

from datetime import date

def query_stocks(
    session: Session,
    stock_query: StockQuery
) -> tuple[date | None, list[StockSnapshotORM]]:
    date_statement = select(
        func.max(StockSnapshotORM.snapshot_date)
    )

    if stock_query.snapshot_date is not None:
        date_statement = date_statement.where(
            StockSnapshotORM.snapshot_date == stock_query.snapshot_date
        )

    snapshot_date = session.scalar(date_statement)

    if snapshot_date is None:
        return None, []

    statement = select(StockSnapshotORM).where(
        StockSnapshotORM.snapshot_date == snapshot_date
    )

    if stock_query.min_change_percent is not None:
        statement = statement.where(
            StockSnapshotORM.change_percent
            >= stock_query.min_change_percent
        )

    if stock_query.max_market_cap is not None:
        statement = statement.where(
            StockSnapshotORM.market_cap
            <= stock_query.max_market_cap
        )

    if stock_query.min_turnover_amount is not None:
        statement = statement.where(
            StockSnapshotORM.turnover_amount
            >= stock_query.min_turnover_amount
        )

    if stock_query.exclude_st:
        statement = statement.where(
            StockSnapshotORM.is_st.is_(False)
        )

    sort_columns = {
        "change_percent": StockSnapshotORM.change_percent,
        "turnover_amount": StockSnapshotORM.turnover_amount,
        "market_cap": StockSnapshotORM.market_cap,
        "turnover_rate": StockSnapshotORM.turnover_rate,
    }

    sort_column = sort_columns[stock_query.sort_by]

    if stock_query.order == "asc":
        statement = statement.order_by(sort_column.asc())
    else:
        statement = statement.order_by(sort_column.desc())

    statement = statement.limit(stock_query.limit)

    stocks = session.scalars(statement).all()

    return snapshot_date, list(stocks)