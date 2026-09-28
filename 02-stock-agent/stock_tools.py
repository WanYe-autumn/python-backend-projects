from schemas import StockQuery


SCREEN_STOCKS_TOOL = {
    "type": "function",
    "function": {
        "name": "screen_stocks",
        "description": (
            "按条件筛选股票，支持AND条件、排序和数量限制。"
            "金额单位为元，涨幅3%写成3。"
            "不支持的要求用supported=false标记，并说明原因。"
        ),
        "parameters": StockQuery.model_json_schema(),
    },
}

if __name__ == "__main__":
    print(SCREEN_STOCKS_TOOL["function"]["parameters"])
    