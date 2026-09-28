from datetime import date

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from database import get_session
from models import StockSnapshotORM

from llm_parser import parse_stock_query
from schemas import NaturalLanguageRequest
from stock_service import query_stocks

from openai import APITimeoutError, OpenAIError
from pydantic import ValidationError

import logging
logger = logging.getLogger("uvicorn.error")

app = FastAPI()


@app.get("/stocks")
def get_stocks(
    min_change_percent: float | None = None,
    max_market_cap: float | None = None,
    min_turnover_amount: float | None = None,
    exclude_st: bool = False,
    sort_by: str = "change_percent",
    order: str = "desc",
    limit: int = 10,
    snapshot_date: date | None = None,
    session: Session = Depends(get_session),
):
    if snapshot_date is None:
        latest_date_statement = select(
            func.max(StockSnapshotORM.snapshot_date)
        )
        snapshot_date = session.scalar(latest_date_statement)

    if snapshot_date is None:
        return []

    statement = select(StockSnapshotORM).where(
        StockSnapshotORM.snapshot_date == snapshot_date
    )

    if min_change_percent is not None:
        statement = statement.where(
            StockSnapshotORM.change_percent >= min_change_percent
        )

    if max_market_cap is not None:
        statement = statement.where(
            StockSnapshotORM.market_cap <= max_market_cap
        )

    if min_turnover_amount is not None:
        statement = statement.where(
            StockSnapshotORM.turnover_amount >= min_turnover_amount
        )

    if exclude_st:
        statement = statement.where(
            StockSnapshotORM.is_st.is_(False)
        )

    sort_column = {
        "change_percent": StockSnapshotORM.change_percent,
        "turnover_amount":StockSnapshotORM.turnover_amount,
        "market_cap":StockSnapshotORM.market_cap,
        "turnover_rate":StockSnapshotORM.turnover_rate,
    }

    sort_column = sort_column.get(
        sort_by,
        StockSnapshotORM.change_percent,
    )

    if order == "asc":
        statement = statement.order_by(sort_column.asc())
    else:
        statement = statement.order_by(sort_column.desc())


    statement = statement.limit(limit)

    stocks = session.scalars(statement).all()

    return stocks

@app.post("/stocks/search")
def search_stocks(
    request: NaturalLanguageRequest,
    session: Session = Depends(get_session),
):
    try:
        stock_query, assistant_message = parse_stock_query(request.query)

    except APITimeoutError:
        raise HTTPException(
        status_code=504,
        detail="模型响应超时，请稍后重试",
    )

    except ValidationError:
        raise HTTPException(
        status_code=502,
        detail="模型返回的筛选条件格式不符合要求",
    )

    except (OpenAIError, RuntimeError):
        logger.exception("模型调用失败")
        raise HTTPException(
        status_code=502,
        detail="模型服务暂时不可用",
    )

    if not stock_query.supported:
        raise HTTPException(
            status_code=422,
            detail=stock_query.unsupported_reason,
        )

    snapshot_date, stocks = query_stocks(
        session=session,
        stock_query=stock_query,
    )

    return {
        "parsed_query": stock_query.model_dump(),
        "snapshot_date": snapshot_date,
        "count": len(stocks),
        "stocks": stocks,
    }