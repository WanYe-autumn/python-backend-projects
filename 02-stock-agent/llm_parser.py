import os
import logging

from dotenv import load_dotenv
from openai import OpenAI

from schemas import StockQuery
from stock_tools import SCREEN_STOCKS_TOOL

logger = logging.getLogger("uvicorn.error")
load_dotenv()

api_key = os.getenv("DEEPSEEK_API_KEY")

if not api_key:
    raise RuntimeError("没有读取到 DEEPSEEK_API_KEY")

client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com",
    timeout=30.0,
    max_retries=0,
)

SYSTEM_PROMPT = """
你是一个A股筛选条件解析器。

你的任务是理解用户的选股要求，通过调用 screen_stocks 工具提交筛选参数。
不支持的要求也通过该工具提交，设置 supported=false，并填写 unsupported_reason。

当前只支持以下条件：
1. snapshot_date：快照日期，格式为 YYYY-MM-DD
2. min_change_percent：最低涨跌幅
3. max_market_cap：最大总市值
4. min_turnover_amount：最低成交额
5. exclude_st：是否排除ST股票
6. sort_by：排序字段
7. order：排序方向
8. limit：返回数量

单位转换规则：
1. 涨跌幅使用百分点。用户说“3%”，输出3，不是0.03。
2. 市值和成交额统一使用元。
3. 1万等于10000。
4. 1亿等于100000000。
5. 100亿等于10000000000。

sort_by只能是：
- change_percent
- turnover_amount
- market_cap
- turnover_rate

order只能是：
- asc
- desc

如果用户使用市盈率、行业、股价、连续上涨天数等当前不支持的指标：
1. supported必须为false
2. unsupported_reason必须说明不支持什么
3. 不能静默忽略不支持的条件

只支持所有筛选条件同时成立（AND）。
如果用户要求“或者 / OR”，或要求当前字段无法表达的比较方向，
必须输出 supported=false，并在 unsupported_reason 中说明原因。
不能把 OR 偷偷改成 AND，也不能忽略无法表达的条件。

调用工具时，参数应包含以下字段：
{
  "supported": true,
  "unsupported_reason": null,
  "snapshot_date": null,
  "min_change_percent": null,
  "max_market_cap": null,
  "min_turnover_amount": null,
  "exclude_st": false,
  "sort_by": "change_percent",
  "order": "desc",
  "limit": 10
}
"""

def parse_stock_query(query: str) -> tuple[dict, StockQuery]:
    response = client.chat.completions.create(
        model="deepseek-flash",
        messages=[
            {
                "role":"system",
                "content":SYSTEM_PROMPT,
            },
            {
                "role":"user",
                "content":query,
            }
        ],
        tools=[SCREEN_STOCKS_TOOL],
        tool_choice={
        "type": "function",
        "function": {"name": "screen_stocks"},
},
        extra_body={"thinking": {"type": "disabled"}},
        max_tokens=1600,
    )

    usage = response.usage

    if usage is not None:
        logger.info(
            "DeepSeek 用量：输入=%s 输出=%s 合计=%s tokens",
            usage.prompt_tokens,
            usage.completion_tokens,
            usage.total_tokens,
        )

    choice = response.choices[0]

    logger.info(
    "DeepSeek 结束原因：%s",
    choice.finish_reason,
    )

    tool_calls = choice.message.tool_calls

    if not tool_calls or len(tool_calls) != 1:
        raise RuntimeError("预期模型返回一次工具调用")

    tool_call = tool_calls[0]

    if tool_call.function.name != "screen_stocks":
        raise RuntimeError("模型请求了未知工具")

    arguments = tool_call.function.arguments
    
    logger.info("工具参数：%s", tool_call.function.arguments)
    logger.info("模型申请调用工具：%s", tool_call.function.name)

    stock_query = StockQuery.model_validate_json(arguments)

    assistant_message = choice.message.model_dump(exclude_none=True)

    return assistant_message, stock_query

if __name__ == "__main__":
    assistant_message, stock_query = parse_stock_query(
        "排除ST，按成交额从高到低取5只"
    )

    print("筛选参数：", stock_query.model_dump())
    print("调用编号：", assistant_message["tool_calls"][0]["id"])