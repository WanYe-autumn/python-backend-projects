import sqlite3
from models import Book

DB_PATH = "library.db"

def init_db(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        price REAL NOT NULL,
        borrowed INTEGER REAL NOT NULL
    )
    """)
    conn.commit()
    conn.close()

def add_book_to_db(book: Book, db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO books (title, author, price, borrowed)
        VALUES(?, ?, ?, ?)
        """,
        (
            book.title,
            book.author,
            book.price,
            book.borrowed
        )
    )

    conn.commit()
    conn.close()

def get_book_from_db(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM books")
    rows = cursor.fetchall()
    conn.close()

    books = [
        Book(
            title=row[1],
            author=row[2],
            price=row[3],
            borrowed=bool(row[4]),
        )
        for row in rows
    ]

    return books

def whether_borrowed_book_in_db(borrowed: bool,db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    if borrowed == True:
        cursor.execute("""
        SELECT * FROM books WHERE borrowed is TRUE
         """)

        rows = cursor.fetchall()
        conn.close()
        books = [
            Book(
                title=row[1],
                author=row[2],
                price=row[3],
                borrowed=bool(row[4]),
            )
            for row in rows
        ]
        return books
    
    elif borrowed == False:
        cursor.execute("""
        SELECT * FROM books WHERE borrowed is FALSE
            """)

        rows = cursor.fetchall()
        conn.close()
        books = [
            Book(
                title=row[1],
                author=row[2],
                price=row[3],
                borrowed=bool(row[4]),
            )
            for row in rows
        ]
        
        return books

def get_book_by_id(number: int, db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT title,author,price,borrowed
        FROM books
        WHERE id = ?
    """,
        (number,)
        )

    row = cursor.fetchone()

    if row is None:
        conn.close()
        return None
    
    book = Book(
        title=row[0],
        author=row[1],
        price=row[2],
        borrowed=bool(row[3])
    )
    conn.close()
    return book
    
def delete_book_from_db_cli(number: int, db_path=DB_PATH):
    if number <= 0:
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id
        FROM books
        ORDER BY id
        LIMIT 1 OFFSET ?
        """,
        (number - 1,)
    )

    row = cursor.fetchone()

    if row is None:
        conn.close()
        return False

    cursor.execute(
        "DELETE FROM books WHERE id = ?",
        (row[0],)
    )

    conn.commit()
    conn.close()

    return True

def delete_book_from_db(book_id: int, db_path=DB_PATH):

    if book_id <= 0:
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()


    cursor.execute(
        "DELETE FROM books WHERE id = ?",
        (book_id,)
    )

    if cursor.rowcount == 0:
        conn.close()
        return False
    conn.commit()
    conn.close()

    return True

def borrow_book_from_db(number: int,db_path=DB_PATH) -> bool:
    if number <= 0:
        return False
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
    SELECT id,borrowed 
    FROM books
    ORDER BY id
    LIMIT 1 OFFSET ?
    """,
    (number - 1,)
    )

    row = cursor.fetchone()
    if row is None:
        conn.close
        return False
    if row[1] == 1:
        conn.close()
        return False

    cursor.execute(
        "UPDATE books SET borrowed = 1 WHERE id = ?",
        (row[0],)
    )
    conn.commit()
    conn.close()
    return True

def return_book_from_db(number: int,db_path=DB_PATH) -> bool:
    if number <= 0:
        return False
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
    SELECT id,borrowed
    FROM books
    ORDER BY id
    LIMIT 1 OFFSET ?
    """,
    (number - 1,)
    )

    row = cursor.fetchone()
    if row is None:
        conn.close()
        return False
    
    if row[1] == 0:
        conn.close()
        return False

    cursor.execute(
        "UPDATE books SET borrowed = 0 WHERE id = ?",
        (row[0],)
    )
    conn.commit()
    conn.close()
    return True

def update_book_in_db(book_id: int, update_data: dict, db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    set_clause = ", ".join(f"{key} = ?" for key in update_data.keys())
    values = list(update_data.values())
    values.append(book_id)

    sql = f"""
    UPDATE books
    SET {set_clause}
    WHERE id = ?
    """

    cursor.execute(sql, values)

    conn.commit()
    conn.close()

def whether_book_in_db(title: str, author: str, db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
            """
        SELECT id
        FROM books
        WHERE title=? AND author=?
        """,
        (title,
         author,)
        )
    row = cursor.fetchone()
    conn.close()
    if not row:
        return False
    return True

def update_price_by_book_id(id: int, price: float, db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute(
        """
    UPDATE books set price = ?
    WHERE id=?
    """,
    (price,id,)
    )
    conn.commit()
    conn.close()
   
