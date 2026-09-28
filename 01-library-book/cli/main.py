from services import add_book,get_quantity_book,get_average_price,get_quantity_borrowed_book,get_qunatity_unborrowed_book
from models import  Book,prase_book_input
from database import init_db,add_book_to_db,get_book_from_db,delete_book_from_db,borrow_book_from_db,return_book_from_db

def display_book(books: list[Book]) -> None:
    if not books:
        print("暂无借阅记录")
        return

    for number, book in enumerate(books, start=1):
        print(
            f"{number}."
            f"{book.title}，"
            f"{book.author}，"
            f"{book.price}，"
            f"{book.borrowed}"
        )

def main() -> None:
    print("图书借阅系统简化版V0.1")

    init_db()
    books = get_book_from_db()

    while True:
        print("\n请选择操作：")
        print("1.新增一本书")
        print("2.查看所有书")
        print("3.删除第N本书")
        print("4.借出一本书")
        print("5.归还一本书")
        print("6.查看统计")
        print("0.退出")

        choice = input("请输入编号：").strip()
        if choice == "1":
            raw_input = input(
                "(请输入:书名,作者,价格,是否已经借出)"
            ).strip()
            try:
                book = prase_book_input(raw_input)
                add_book_to_db(book)
                print(f"添加成功并已保存：{book}")

            except ValueError as e:
                print(f"输入错误：{e}")

            books = get_book_from_db()
            continue

        elif choice == "2":
            display_book(books)
            continue

        elif choice == "3":
            display_book(books)

            if not books:
                continue

            try:
                number = int(input("请输入要删除的编号："))
            except ValueError:
                print("输入编号必须为整数")
                continue

            confirm = input(
                f"确定删除第{number} 本书吗？输入 y 确认："
            ).strip().lower()

            if confirm != "y":
                print("已取消删除")
                continue

            success = delete_book_from_db(number)

            if not success:
                print("编号不存在")
                continue

            books = get_book_from_db()

            print(f"已删除并保存:{book}")
            continue

        elif choice == "4":
            display_book(books)

            if not books:
                continue

            try:
                number = int(input("请输入要借书的编号："))
            except ValueError:
                print("输入编号必须是整数")
                continue

            success_borrowed = borrow_book_from_db(number)

            if success_borrowed:
                print("借阅成功")
                books = get_book_from_db()
                continue

            if not success_borrowed:
                print("借阅失败")
                continue

            

        elif choice == "5":
            display_book(books)
            
            if not books:
                continue

            try:
                number = int(input("请输入要还书的编号:"))
            except ValueError:
                print("输入编号必须是整数")
                continue

            success_returned = return_book_from_db(number)

            if not success_returned:
                print("还书失败")

            if success_returned:
                print("还书成功")
            books = get_book_from_db()

        elif  choice == "6":
            total_quantity = get_quantity_book(books)
            print(f"总书数:{total_quantity}")
            quantity_borrowed = get_quantity_borrowed_book(books)
            print(f"已借出数量:{quantity_borrowed}")
            quantity_unborrowed = get_qunatity_unborrowed_book(books)
            print(f"未借出数量:{quantity_unborrowed}")
            avg_price = get_average_price(books)
            print(f"平均价格:{avg_price}")

        elif choice == "0":
            break

        else:
            print("无效选项,请输入0-6")
                


if __name__ == "__main__":
    main()