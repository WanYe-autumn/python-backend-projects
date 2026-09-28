import os
import time
from datetime import datetime

import akshare as ak
from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import engine
from models import StockSnapshotORM


load_dotenv()

token = os.getenv("XQ_A_TOKEN")

if not token:
    raise RuntimeError("没有读取到 XQ_A_TOKEN")


stock_symbols = [
    "SH600036",  # 招商银行
    "SH600519",  # 贵州茅台
    "SH601318",  # 中国平安
    "SH600900",  # 长江电力
    "SH601012",  # 隆基绿能
    "SZ000858",  # 五粮液
    "SZ000333",  # 美的集团
    "SZ002594",  # 比亚迪
    "SZ300750",  # 宁德时代
    "SZ000001",  # 平安银行
]


with Session(engine) as session:
    for symbol in stock_symbols:
        try:
            print("正在获取：", symbol)

            stock_data = ak.stock_individual_spot_xq(
                symbol=symbol,
                token=token,
                timeout=15,
            )

            stock_dict = dict(
                zip(stock_data["item"], stock_data["value"])
            )

            snapshot_time = datetime.strptime(
                str(stock_dict["时间"]),
                "%Y-%m-%d %H:%M:%S",
            )

            stock_record = {
                "stock_code": stock_dict["代码"],
                "stock_name": stock_dict["名称"],
                "close_price": float(stock_dict["现价"]),
                "change_percent": float(stock_dict["涨幅"]),
                "turnover_amount": float(stock_dict["成交额"]),
                "market_cap": float(stock_dict["资产净值/总市值"]),
                "turnover_rate": float(stock_dict["周转率"]),
                "is_st": "ST" in str(stock_dict["名称"]).upper(),
                "snapshot_date": snapshot_time.date(),
                "data_source": "xueqiu",
            }

            statement = select(StockSnapshotORM).where(
                StockSnapshotORM.stock_code
                == stock_record["stock_code"],
                StockSnapshotORM.snapshot_date
                == stock_record["snapshot_date"],
            )

            existing_stock = session.scalars(statement).first()

            if existing_stock is not None:
                print(
                    "当天数据已存在：",
                    stock_record["stock_code"],
                    stock_record["stock_name"],
                )
            else:
                stock = StockSnapshotORM(**stock_record)

                session.add(stock)
                session.commit()
                session.refresh(stock)

                print(
                    "写入成功：",
                    stock.id,
                    stock.stock_code,
                    stock.stock_name,
                )

            # 避免短时间内连续请求雪球
            time.sleep(1)

        except Exception as error:
            session.rollback()
            print("导入失败：", symbol, error)