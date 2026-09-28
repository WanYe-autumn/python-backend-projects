from sqlalchemy import create_engine, String, Float, Boolean, text, select, DateTime, ForeignKey, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from datetime import datetime
from config import DATABASE_URL

engine = create_engine(DATABASE_URL)
# Engine 主要知道：
# - 数据库在哪里；
# - 用什么驱动连接；
# - 如何管理数据库连接。
def get_session():
    with Session(engine) as session:
        yield session

class Base(DeclarativeBase):
    pass

class BookORM(Base):
    __tablename__ = "books"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    author: Mapped[str] = mapped_column(String(100))
    price: Mapped[float] = mapped_column(Float)
    borrowed: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
# Base.metadata.create_all(engine)

# with Session(engine) as session:
#     book = BookORM(title="Python", author="A", price=88.0, borrowed=False)
#     session.add(book)
#     session.commit()
#     print(book.id, book.title)

# with Session(engine) as session:
#     statement = select(BookORM)
#     books = session.scalars(statement).all()
#     for book in books:
#         print(book.id, book.title, book.author, book.price, book.borrowed)

# with engine.connect() as conn:
#     result = conn.execute(text("SELECT current_database()"))
#     print(result.scalar())

class UserORM(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))

class BorrowRecordORM(Base):
    __tablename__ = "borrow_records"
    __table_args__ = (
        Index(
            "uq_borrow_records_active_book",
            "book_id",
            unique=True,
            postgresql_where=text("return_date IS NULL"),
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    borrow_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    return_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)