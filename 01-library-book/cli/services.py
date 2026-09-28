from models import Book


def get_quantity_book(books: list[Book]) -> int:
    return len(books)

def get_quantity_borrowed_book(books: list[Book]) -> int:
    quantity = 0
    for book in books:
        if book.borrowed:
            quantity += 1
    return quantity

def get_qunatity_unborrowed_book(books: list[Book]) -> int:
    quantity = len(books) - get_quantity_borrowed_book(books)
    return quantity

def get_average_price(books: list[Book]) -> float:
    if not books:
        return 0.0

    total_price = 0

    for book in books:
        total_price += book.price

    return total_price/len(books)

def make_borrowed_book_true(books: list[Book],number: int):
    if number <= 0 or number > len(books):
     raise ValueError

    book = books[number - 1]

    if book.borrowed:
        raise ValueError

    book.borrowed = True

def return_book(books: list[Book],number: int):
    if number <= 0 or number > len(books):
        raise ValueError

    book = books[number - 1]

    if book.borrowed == False:
        raise ValueError

    book.borrowed = False

def add_book(books: list[Book], book: Book) -> None:
    if book.title == "" or book.price < 0:
        raise ValueError

    books.append(book)

def delete_book(books: list[Book], number: int) -> Book:
    if number <= 0 or number > len(books):
        raise ValueError
    deleted_book = books.pop(number - 1)

    return deleted_book

        