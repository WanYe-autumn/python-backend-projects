import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL is None:
    raise RuntimeError("DATABASE_URL 未配置")

engine = create_engine(DATABASE_URL)


class Base(DeclarativeBase):
    pass


def get_session():
    with Session(engine) as session:
        yield session