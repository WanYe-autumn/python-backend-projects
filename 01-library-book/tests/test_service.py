from services import add_book,delete_book,make_borrowed_book_true,return_book,get_average_price,get_quantity_borrowed_book
from models import Book
import pytest

def test_add_book():
    books = []

    book = Book(
        title="python入门",
        author="A",
        price=69.9,
        borrowed=False
    )

    add_book(books,book)

    assert len(books) == 1
    assert books[0] == book

def test_delete_book():
    books = [
        Book(
        title="python入门",
        author="A",
        price=69.9,
        borrowed=False
    )
    ]
    deleted_book = delete_book(books,1)
    assert deleted_book.title == "python入门"
    assert books == []

def test_ValueReeoe():
    books = [
        Book(
          title="python入门",
          author="A",
          price=69.9,
          borrowed=False  
        )
    ]

    with pytest.raises(ValueError):
        delete_book(books,0)

def test_get_average_price():
    books = [
         Book("A", "作者1", 69, False),
         Book("B", "作者2", 31, False),
    ]
    
    result = get_average_price(books)
    assert result == pytest.approx(50.0)

def test_get_quantity_borrowed_book():
    books = [
             Book("A", "作者1", 69, False),
             Book("B", "作者2", 31, True),
             Book("C", "作者2", 31, True),
        ]

    quantity_borrowed_book = get_quantity_borrowed_book(books)
    assert quantity_borrowed_book == 2

def test_delete_book_invalid_number():
    books = [Book("A", "作者1", 69, False)]
    with pytest.raises(ValueError):
        delete_book(books,99) 
    