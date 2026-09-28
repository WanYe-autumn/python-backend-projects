from dataclasses import dataclass

@dataclass
class Book:
    title: str
    author: str
    price: float
    borrowed: bool

def prase_book_input(raw_input: str) -> Book:
    raw_input = raw_input.replace("，", ",").replace("；", ";")
    fields = raw_input.split(",")

    if len(fields) != 4:
        raise ValueError("请输入：书名,作者,价格,是否已经借出")

    title = fields[0].strip()
    author = fields[1].strip()
    try:
        price = float(fields[2])
    except ValueError:
        raise ValueError("价格必须是数字")
        

    if title == "":
        raise ValueError("书名不能为空")

    if author == "":
        raise ValueError("作者名不能为空")
    
    if price <= 0 :
        raise ValueError("价格必须大于零")

    if fields[3] == "1":
        borrowed = True
    elif fields[3] == "0":
        borrowed = False
    else:
        raise ValueError("是否借出必须输入0或1")

    return Book(
    title=title,
    author=author,
    price=price,
    borrowed=borrowed    
    )
    
