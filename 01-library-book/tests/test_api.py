from fastapi.testclient import TestClient
from app import app
# from database import init_db,add_book_to_db
import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from orm_demo import Base, get_session, BookORM, UserORM, BorrowRecordORM
from security import create_access_token
from datetime import datetime, timezone

TEST_DATABASE_URL = os.environ["TEST_DATABASE_URL"]
test_engine = create_engine(TEST_DATABASE_URL)

@pytest.fixture
def test_db():
    Base.metadata.drop_all(test_engine)
    Base.metadata.create_all(test_engine)

    yield test_engine

    Base.metadata.drop_all(test_engine)

@pytest.fixture
def client(test_db):
    def override_get_session():
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()

@pytest.fixture
def create_book(test_db):
    def _create_book(
        title="Python",
        author="A",
        price=88.0,
        borrowed=False,
    ):
        with Session(test_engine) as session:
            book = BookORM(
                title=title,
                author=author,
                price=price,
                borrowed=borrowed,
            )
            session.add(book)
            session.commit()
            session.refresh(book)
            return book.id

    return _create_book

# @pytest.fixture
# def create_user(test_db):
#     def _create_user(username="testuser", password_hash="hashedpassword"):
#         with Session(test_engine) as session:
#             user = UserORM(
#                 username=username,
#                 password_hash=password_hash,
#             )
#             session.add(user)
#             session.commit()
#             session.refresh(user)
#             return user.id

#     token = create_access_token(user.id)

#     return {
#     "id": user.id,
#     "headers": {
#         "Authorization": f"Bearer {token}",
#     },
# }
@pytest.fixture
def create_user(test_db):
    def _create_user(username="testuser", password_hash="hashedpassword"):
        with Session(test_engine) as session:
            user = UserORM(
                username=username,
                password_hash=password_hash,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            return user.id

    return _create_user

def test_books(client):
    response = client.get("/books")

    assert response.status_code == 200
    assert response.json() == []

def test_get_books_by_id_a(client, create_book):
    book_id = create_book(title="haha", author="zuojia1", price=30.0, borrowed=True)

    # 再请求刚才创建的书
    response = client.get(f"/books/{book_id}")
    data = response.json()

    assert response.status_code == 200
    assert data["id"] == book_id
    assert data["title"] == "haha"
    assert data["author"] == "zuojia1"
    assert data["price"] == 30.0
    assert data["borrowed"] is True

def test_get_book_not_found(test_db,client):
    response = client.get("/books/999")

    assert response.status_code == 404

def test_query_parameter_true(test_db,client):
    with Session(test_engine) as session:
        book = BookORM(
        title="haha",
        author="zuojia1",
        price=30.0,
        borrowed=True,
    )

        session.add(book)
        session.commit()
        session.refresh(book)

        book_id = book.id

    response = client.get("/books?borrowed=true")

    assert response.status_code == 200
    assert response.json() == [{
        "id": book_id,
        "title": "haha",
        "author": "zuojia1",
        "price": 30.0,
        "borrowed": True,
        "description": None
    }]

def test_query_parameter_false(client, create_book):
    book_id = create_book(title="haha", author="zuojia1", price=30.0, borrowed=False)

    response = client.get("/books?borrowed=false")

    assert response.status_code == 200
    assert response.json() == [{
        "id": book_id,
        "title": "haha",
        "author": "zuojia1",
        "price": 30.0,
        "borrowed": False,
        "description": None
    }]

def test_post_create_book(client, test_db):

    response = client.post(
    "/books",
    json={
        "title": "Python",
        "author": "A",
        "price": 88
    }
)
    assert response.status_code == 200

    data = response.json()
    book_id = data["id"]

    assert data == {
    "id": book_id,
    "title": "Python",
    "author": "A",
    "price": 88.0,
    "borrowed": False,
    "description": None
}

    get_response = client.get("/books")

    assert get_response.status_code == 200
    assert get_response.json() ==  [
    {
        "id": book_id,
        "title": "Python",
        "author": "A",
        "price": 88.0,
        "borrowed": False,
        "description": None
    }
]

def test_post_create_book_yichang1(test_db,client):
    response = client.post(
        "/books",
        json={
            "title": "Python",
            "author": "B",
        }
    )
    assert response.status_code == 422

def test_post_create_book_yichang2(test_db,client):
    response = client.post(
        "/books",
        json={
            "title": "Python",
            "author": "B",
            "price": -1
        }
    )
    assert response.status_code == 422

def test_post_create_book_yichang3(test_db,client):
    book = BookORM(title="haha",author="zuojia1",price=30,borrowed=False)
    with Session(test_engine) as session:
        session.add(book)
        session.commit()
        session.refresh(book)
        book_id = book.id
    response = client.post(
        "/books",
        json={
            "id": book_id,
            "title": "haha",
            "author": "zuojia1",
            "price": 30
        }
    )
    assert response.status_code == 409

def test_patch_update_book(create_book,client):
    book_id = create_book(title="haha", author="zuojia1", price=30, borrowed=False)

    response = client.patch(
        f"/books/{book_id}",
        json={
            "title": "djh"
        }
    )
    assert response.status_code == 200
    assert response.json() == {
        "id": book_id,
        "title": "djh",
        "author": "zuojia1",
        "price": 30,
        "borrowed": False,
        "description": None
    }

    get_response = client.get(f"/books/{book_id}")

    assert get_response.status_code == 200
    assert get_response.json() == {
        "id": book_id,
        "title": "djh",
        "author": "zuojia1",
        "price": 30,
        "borrowed": False,
        "description": None
    }

def test_delete_book(test_db,client):
    book = BookORM(title="hahaha", author="djh", price=30, borrowed=True)
    with Session(test_engine) as session:
        session.add(book)
        session.commit()
        session.refresh(book)
    response = client.delete(
        "books/1",
    )
    assert response.status_code == 200
    get_response = client.get("/books/1")
    assert get_response.status_code == 404

def test_delete_book_404(test_db,client):
    response = client.delete("/books/999")
    assert response.status_code == 404

def test_patch_price_200(test_db,client):
    book=BookORM(title="niulai", author="djh", price="77.0", borrowed=False)
    with Session(test_engine) as session:
        session.add(book)
        session.commit()
        session.refresh(book)
    response = client.patch(
        "/books/1/price",
        json={"price":666})

    assert response.status_code == 200
    get_response = client.get("/books/1")
    assert get_response.status_code == 200
    assert get_response.json()["price"] == 666

@pytest.mark.parametrize("invalid_price",[0,-1])
def test_patch_price_422(client,test_db,invalid_price):
    response = client.patch(
        "/books/1/price",
        json={"price": invalid_price}
    )

    assert response.status_code == 422

def test_patch_price_404(client,test_db):
    response = client.patch(
        "/books/999/price",
        json={"price":600})

    assert response.status_code == 404

def test_patch_price_409(test_db,client):
    book=BookORM(title="niulai", author="djh", price="77.0", borrowed=True)
    with Session(test_engine) as session:
        session.add(book)
        session.commit()
        session.refresh(book)
    response = client.patch(
        "/books/1/price",
        json={"price":600})

    assert response.status_code == 409

def test_get_first_page_of_books(
    client,
    create_book,
    create_user,
):
    user_id = create_user()

    book_ids = [
        create_book(
            title=f"Book {i + 1}",
            author="Author",
            price=10.0,
            borrowed=True,
        )
        for i in range(3)
    ]

    with Session(test_engine) as session:
        for book_id in book_ids:
            record = BorrowRecordORM(
                book_id=book_id,
                user_id=user_id,
                borrow_date=datetime.now(timezone.utc),
                return_date=None,
            )
            session.add(record)

        session.commit()

    token = create_access_token(user_id)

    response = client.get(
        "/users/me/books?limit=2&offset=0",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["id"] == book_ids[2]
    assert data[1]["id"] == book_ids[1]

def test_get_next_page_of_books(
    client,
    create_book,
    create_user,
):
    user_id = create_user()

    book_ids = [
        create_book(
            title=f"Book {i + 1}",
            author="Author",
            price=10.0,
            borrowed=True,
        )
        for i in range(3)
    ]

    with Session(test_engine) as session:
        for book_id in book_ids:
            record = BorrowRecordORM(
                book_id=book_id,
                user_id=user_id,
                borrow_date=datetime.now(timezone.utc),
                return_date=None,
            )
            session.add(record)

        session.commit()

    token = create_access_token(user_id)

    response = client.get(
        "/users/me/books?limit=2&offset=2",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == book_ids[0]

@pytest.mark.parametrize(
    "query_string",
    [
        "limit=0&offset=0",
        "limit=101&offset=0",
        "limit=20&offset=-1",
    ],
)
def test_get_my_books_invalid_parameters(
    client,
    create_user,
    query_string,
):
    user_id = create_user()
    token = create_access_token(user_id)

    response = client.get(
        f"/users/me/books?{query_string}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 422

def test_get_my_books_without_login(client):
    response = client.get(
        "/users/me/books?limit=20&offset=0"
    )

    assert response.status_code == 401

def test_other_users_books_are_not_visible(
    client,
    create_book,
    create_user,
):
    user_a_id = create_user(username="user_a")
    user_b_id = create_user(username="user_b")

    book_a_id = create_book(
        title="User A Book",
        author="Author A",
        price=10.0,
        borrowed=True,
    )
    book_b_id = create_book(
        title="User B Book",
        author="Author B",
        price=20.0,
        borrowed=True,
    )

    with Session(test_engine) as session:
        session.add_all([
            BorrowRecordORM(
                book_id=book_a_id,
                user_id=user_a_id,
                borrow_date=datetime.now(timezone.utc),
                return_date=None,
            ),
            BorrowRecordORM(
                book_id=book_b_id,
                user_id=user_b_id,
                borrow_date=datetime.now(timezone.utc),
                return_date=None,
            ),
        ])
        session.commit()

    token = create_access_token(user_a_id)

    response = client.get(
        "/users/me/books?limit=20&offset=0",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == book_a_id
    assert data[0]["id"] != book_b_id