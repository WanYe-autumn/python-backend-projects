from pathlib import Path

from fastapi import FastAPI,HTTPException,Depends,Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from models import BookORM,get_session,UserORM,BorrowRecordORM
from datetime import datetime, timezone
from jwt.exceptions import InvalidTokenError
from security import hash_password, verify_password, create_access_token, decode_access_token
from pydantic import BaseModel, Field,ConfigDict
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.INFO)

app = FastAPI()

# Set up HTTPBearer for token authentication
bearer = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    session: Session = Depends(get_session),
) -> UserORM:
    auth_error = HTTPException(
        status_code=401,
        detail="登录凭证无效或已过期",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise auth_error

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(payload["sub"])
    except (InvalidTokenError, ValueError, TypeError):
        raise auth_error

    current_user = session.get(UserORM, user_id)

    if current_user is None:
        raise auth_error

    return current_user

@app.get("/users/me")
def read_current_user(
    current_user: UserORM = Depends(get_current_user),
):
    return {
        "id": current_user.id,
        "username": current_user.username,
    }

class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=100)

class BorrowRecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    book_id: int
    user_id: int
    borrow_date: datetime
    return_date: datetime | None


# 查看自己的全部借阅记录，包括已归还的历史记录
@app.get("/borrow-records", response_model=list[BorrowRecordRead])
def get_my_borrow_records(
    session: Session = Depends(get_session),
    current_user: UserORM = Depends(get_current_user),
):
    statement = (
        select(BorrowRecordORM)
        .where(BorrowRecordORM.user_id == current_user.id)
        .order_by(BorrowRecordORM.id.desc())
    )

    records = session.scalars(statement).all()
    return records


@app.post("/users")
def create_user(user: UserCreate, session: Session = Depends(get_session)):
    # Check if the username already exists
    statement = select(UserORM).where(UserORM.username == user.username)
    existing_user = session.scalars(statement).first()
    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Username already exists"
        )

    # Hash the password
    hashed_password = hash_password(user.password)

    # Create a new user
    new_user = UserORM(username=user.username, password_hash=hashed_password)
    session.add(new_user)
    session.commit()
    session.refresh(new_user)

    return {"id": new_user.id, "username": new_user.username}

class UserLogin(BaseModel):
    username: str
    password: str

@app.post("/login")
def login(user: UserLogin, session: Session = Depends(get_session)):
    # Check if the username exists
    statement = select(UserORM).where(UserORM.username == user.username)
    existing_user = session.scalars(statement).first()
    if not existing_user:
        raise HTTPException(
            status_code=401,
            detail="用户名或密码错误"
        )
    # Verify the password
    if not verify_password(user.password, existing_user.password_hash):
        raise HTTPException(
            status_code=401,
            detail="用户名或密码错误"
        )
    access_token = create_access_token(existing_user.id)

    logger.info(
    "Login succeeded: user_id=%s username=%s",
    existing_user.id,
    existing_user.username,
    )

    return {"message": "Login successful", "id": existing_user.id, "username": existing_user.username, "token":access_token, "token_type": "bearer"}

class BookCreate(BaseModel):
    title: str
    author: str
    price: float = Field(gt=0)


class BookUpdate(BaseModel):
    title: str | None = None
    author: str | None = None



class BookPriceUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    price: float = Field(gt=0)

class BookBorrowedUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    borrowed: bool

@app.post("/books")                             # 增书
def create_book(book: BookCreate, session: Session = Depends(get_session)):
    statement = select(BookORM).where(BookORM.title == book.title, BookORM.author == book.author)
    exists = session.scalars(statement).first()
    if exists:
        raise HTTPException(
            status_code=409,
            detail="Book already exists"
        )
    new_book = BookORM(
        title=book.title,
        author=book.author,
        price=book.price,
        borrowed=False
    )
    session.add(new_book)
    session.commit()
    session.refresh(new_book)
    return new_book

@app.delete("/books/{book_id}")                 #删书
def delete_book(book_id: int, session: Session = Depends(get_session)):
    book = session.get(BookORM, book_id)
    if book is None:
        raise HTTPException(
            status_code=404,
            detail="Book not found"
        )
    session.delete(book)
    session.commit()
    return {"message": "Book deleted successfully"}

@app.patch("/books/{book_id}")                  #更新书
def update_book(book_id: int, book_update: BookUpdate, session: Session = Depends(get_session)):
    book = session.get(BookORM, book_id)
    if book is None:
        raise HTTPException(
            status_code=404,
            detail="Book not found"
        )
    update_data = book_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if value is None:
            raise HTTPException(
                status_code=422,
                detail=f"Field '{field}' cannot be updated to None"
            )
        setattr(book, field, value)

    session.commit()
    session.refresh(book)
    return book


@app.get("/books/{book_id}")                    #查书
def get_book(book_id: int, session: Session = Depends(get_session)):
    book = session.get(BookORM, book_id)
    if book is None:
        raise HTTPException(
            status_code=404,
            detail="Book not found"
        )
    return book

@app.get("/books")                              #按借阅状态筛选图书
def get_books_by_borrowed(borrowed: bool | None = None, session: Session = Depends(get_session)):
    statement = select(BookORM)
    if borrowed is not None:
        statement = statement.where(BookORM.borrowed == borrowed)

    books = session.scalars(statement).all()
    return books

@app.patch("/books/{book_id}/price")            #更新书价格
def update_book_price(book_id:int, book_update: BookPriceUpdate, session: Session = Depends(get_session)):
    book = session.get(BookORM, book_id)
    if not book:
        raise HTTPException(
            status_code=404,
            detail="书本不存在"
        )
    borrowed = book.borrowed
    if borrowed:
        raise HTTPException(
            status_code=409,
            detail="禁止修改，书本已经借出"
        )
    book.price = book_update.price
    session.commit()
    session.refresh(book)
    return book

@app.patch("/books/{book_id}/borrowed")            #更新书借阅状态
def update_book_borrowed(book_id:int, book_update: BookBorrowedUpdate, session: Session = Depends(get_session), current_user: UserORM = Depends(get_current_user)):
    # 1. 查询图书，并锁住这一行直到事务结束
    book = session.get(BookORM, book_id, with_for_update=True)
    if not book:
        raise HTTPException(
            status_code=404,
            detail="书本不存在"
        )

    # 2. 查这本书当前未归还的借阅记录
    statement = select(BorrowRecordORM).where(
        BorrowRecordORM.book_id == book_id,
        BorrowRecordORM.return_date == None
    )
    record = session.scalars(statement).first()

    # 3. 借书
    if book_update.borrowed:
        if book.borrowed or record is not None:
            raise HTTPException(status_code=409, detail="该书已借出")

        new_record = BorrowRecordORM(
            book_id=book.id,
            user_id=current_user.id,
            borrow_date=datetime.now(timezone.utc),
            return_date=None,
        )
        session.add(new_record)
        book.borrowed = True

    # 4. 还书
    else:
        if record is None:
            raise HTTPException(
                status_code=409,
                detail="没有未归还的借阅记录，无法归还",
            )

        if record.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="只能归还自己借的书",
            )

        record.return_date = datetime.now(timezone.utc)
        book.borrowed = False

    # 5. 图书状态和借阅记录一起提交
    try:
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise

    session.refresh(book)
    return book

@app.get("/users/me/books")  # 查看自己借的书
def get_my_books(
    session: Session = Depends(get_session),
    current_user: UserORM = Depends(get_current_user),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    statement = (
        select(BookORM).join(
    BorrowRecordORM,
    BorrowRecordORM.book_id == BookORM.id,
        )
        .where(BorrowRecordORM.user_id == current_user.id,
               BorrowRecordORM.return_date.is_(None)
                )
        .order_by(BorrowRecordORM.id.desc())
        .limit(limit)
        .offset(offset)
    )

    books = session.scalars(statement).all()
    return books


FRONTEND_DIR = Path(__file__).resolve().parent / "frontend"


@app.get("/")
def library_home():
    return FileResponse(FRONTEND_DIR / "index.html")


app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR),
    name="frontend",
)