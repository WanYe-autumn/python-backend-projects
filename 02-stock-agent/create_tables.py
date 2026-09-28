from database import Base, engine
from models import StockSnapshotORM


Base.metadata.create_all(engine)

print("stock_snapshots 表创建成功")