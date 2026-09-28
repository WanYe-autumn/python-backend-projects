from database import add_book_to_db,init_db,get_book_from_db,delete_book_from_db,borrow_book_from_db,return_book_from_db
from models import Book
import pytest
def test_add_book_to_db(tmp_path):
    db_path = tmp_path / "test.db"

    init_db(db_path)
    book = Book(title="haha",author="zuojia1",price=30,borrowed=True)
    add_book_to_db(book,db_path)
    result = get_book_from_db(db_path)

    assert len(result) == 1
    assert result[0] == book

def test_delete_book_from_db(tmp_path):
    db_path = tmp_path / "test.db"

    init_db(db_path)  
    book1 = Book(title="haha",author="zuojia1",price=30,borrowed=True)
    book2 = Book(title="hahaha",author="zuojia2",price=30,borrowed=True)
    add_book_to_db(book1,db_path)
    add_book_to_db(book2,db_path)

    delete_book_from_db(1,db_path)
    result = get_book_from_db(db_path)

    assert len(result) == 1
    assert result[0] == book2

def test_borrow_book_from_db(tmp_path):
    db_path = tmp_path / "test.db"

    init_db(db_path)
    book1 = Book(title="haha",author="zuojia1",price=30,borrowed=False)
    book2 = Book(title="hahaha",author="zuojia2",price=30,borrowed=False)
    add_book_to_db(book1,db_path)
    add_book_to_db(book2,db_path)

    borrow_book_from_db(1,db_path)
    result = get_book_from_db(db_path)
    
    assert result[0].borrowed == True
    assert result[1].borrowed == False

def test_return_book_from_db(tmp_path):
    db_path = tmp_path / "test.db"

    init_db(db_path)
    book1 = Book(title="haha",author="zuojia1",price=30,borrowed=False)
    book2 = Book(title="hahaha",author="zuojia2",price=30,borrowed=True)
    add_book_to_db(book1,db_path)
    add_book_to_db(book2,db_path)

    return_book_from_db(2,db_path)
    result = get_book_from_db(db_path)

    assert result[0].borrowed == False
    assert result[1].borrowed == False

def test_borrow_book_twice(tmp_path):
    db_path = tmp_path / "test.db"
    
    init_db(db_path)
    book1 = Book(title="haha",author="zuojia1",price=30,borrowed=False)
    book2 = Book(title="hahaha",author="zuojia2",price=30,borrowed=False)
    add_book_to_db(book1,db_path)
    add_book_to_db(book2,db_path)



    returned1 = borrow_book_from_db(1,db_path)
    returned2 = borrow_book_from_db(1,db_path)

    assert returned1 == True
    assert returned2 == False

    result = get_book_from_db(db_path)

    assert result[0].borrowed == True
 


    