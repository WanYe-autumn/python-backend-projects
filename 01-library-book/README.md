# 图书管理 API

使用 Python、FastAPI 和 SQLite 实现的后端学习项目。从图书借阅命令行程序逐步扩展为 HTTP API，并通过 pytest 验证接口、数据库操作和业务函数。

当前进度：完成 Day8 的测试数据隔离、客户端 fixture、修改后重新查询断言与价格边界参数化。后续在现有项目上学习 PostgreSQL、ORM、鉴权和部署。

## 已实现功能

- 新增图书：校验必填字段和正数价格；书名、作者同时重复时返回冲突。
- 查询全部图书、指定 ID 的图书，以及按借阅状态筛选。
- 局部修改图书信息、按 ID 删除图书。
- 专用改价接口：先检查图书是否存在，再检查是否已借出，允许修改时更新数据库并返回图书。
- 数据库层支持借书、还书；业务函数支持数量、借阅数量和平均价格统计。
- 保留早期命令行入口，其已知问题见文末；当前主要演示入口为 API。

## 技术与结构

Python、FastAPI、Pydantic、SQLite、pytest、TestClient；使用 Uvicorn 启动 HTTP 服务。

| 路径 | 职责 |
| --- | --- |
| `app.py` | FastAPI 路由、请求模型与接口规则 |
| `database.py` | SQLite 建表、查询和数据修改 |
| `models.py` | `Book` 数据类与命令行输入解析 |
| `services.py` | 列表操作、借还状态和统计函数 |
| `main.py` | 早期命令行交互入口 |
| `tests/test_api.py` | API 测试与 fixture |
| `tests/test_database.py` | 数据库测试 |
| `tests/test_service.py` | 业务函数测试 |

目前路由直接调用数据库函数；`services.py` 主要保留早期列表业务逻辑，尚未统一为 API 的业务层。

## 本地运行

以下命令在 `01-library-book` 目录执行，使用已经安装项目依赖的 Python 虚拟环境。已知本机测试环境为 Python 3.12.13；当前尚未提交锁定版本的依赖清单，新环境的完整安装复现仍待补充。

首次启动先创建开发数据库及表：

```bash
python -c "from database import init_db; init_db()"
```

启动服务：

```bash
python -m uvicorn app:app --reload
```

打开 [Swagger 接口文档](http://127.0.0.1:8000/docs)，可直接发送请求。

开发数据库默认是当前工作目录中的 `library.db`。不需要下载演示数据库，初始化命令即可创建空库。API 启动时不会自动建表，因此首次启动不能省略初始化。

## 接口说明

| 方法 | 路径 | 功能 |
| --- | --- | --- |
| POST | `/books` | 新增图书 |
| GET | `/books` | 查询全部图书 |
| GET | `/books?borrowed=true` | 查询已借出图书，`false` 表示未借出 |
| GET | `/books/{book_id}` | 按数据库 ID 查询 |
| PATCH | `/books/{book_id}` | 局部修改图书字段 |
| PATCH | `/books/{book_id}/price` | 通过专用业务规则修改价格 |
| DELETE | `/books/{book_id}` | 按数据库 ID 删除 |

### 新增与改价示例

通过 `POST /books` 提交：

```json
{
  "title": "Python入门",
  "author": "A",
  "price": 30
}
```

成功返回 `200` 和图书数据，未传 `borrowed` 时默认为 `false`。

在全新空库中新增的第一本书通常为 ID 1。通过 `PATCH /books/1/price` 提交：

```json
{
  "price": 66
}
```

成功返回 `200`：

```json
{
  "title": "Python入门",
  "author": "A",
  "price": 66.0,
  "borrowed": false
}
```

再请求 `GET /books/1`，可确认修改已经保存。已有数据库中的 ID 不一定是 1；当前图书响应尚未包含 ID 字段。

### 专用改价接口状态码

| 状态码 | 场景 |
| --- | --- |
| 200 | 图书存在且未借出，修改成功 |
| 404 | 传入合法价格，但图书不存在 |
| 409 | 图书已借出，禁止修改价格 |
| 422 | 价格为 0、负数等请求校验失败 |

Pydantic 在进入路由函数前校验请求。因此价格为 0 或负数时，即使图书不存在，也会先返回 422。

通用 PATCH 成功返回 `book_id` 和 `update` 字典；DELETE 成功返回 JSON 布尔值 `true`。两者与专用改价接口的响应结构不同。

## 自动化测试

执行全部测试：

```bash
python -m pytest -q
```

仅执行改价成功测试或非法价格测试：

```bash
python -m pytest -v -k test_patch_price_200
python -m pytest -v -k test_patch_price_422
```

2026-09-10 本机运行记录：**28 passed，1 warning**。此结果来自开发者提供的终端运行截图，未表示所有边界条件均已覆盖。warning 为 TestClient 依赖的弃用提醒，未造成该次测试失败。

| 测试类别 | 用例数（含参数化展开） | 主要内容 |
| --- | --- | --- |
| API | 17 | 查询、筛选、新增、重复数据、修改、删除、改价规则 |
| 数据库 | 5 | 新增、删除、借书、还书、重复借书 |
| 业务函数 | 6 | 新增、删除、非法编号、平均价格与借阅数量 |

### 测试库隔离

`test_db` fixture 使用 `tmp_path` 提供的临时目录，创建 `test.db` 和表，再通过 `monkeypatch` 临时修改 `app.DB_PATH`。

`client` fixture 依赖 `test_db`，确保数据库先准备好，再创建 TestClient。`yield` 将客户端交给当前用例，测试结束后退出 `with` 并关闭客户端；`monkeypatch` 自动恢复应用原配置。临时目录由 pytest 管理，不要求每次测试结束立即删除文件。

- 直接调用数据库函数准备数据：明确传入 `test_db`，避免使用默认开发库。
- 通过客户端请求 API：路由把已经替换的 `DB_PATH` 传给数据库函数。
- 同一用例内，两种方式操作同一个测试库；默认每条用例有独立初始数据。

### Day8 的测试改进

- 修改成功后重新 GET，并断言价格，检查持久化结果。
- 使用 `@pytest.mark.parametrize` 分别验证 0 和负数返回 422。
- 修正查询路径 `/book/1` 为 `/books/1`，避免请求错误路由。

## 已知限制与待修复项

以下为当前代码检查发现的边界，后续逐项补充实现和测试：

- 尚无鉴权、用户数据隔离及独立 HTTP 借还书接口。
- 通用 PATCH 未检查目标是否存在，也未妥善处理空请求体和显式 `null`。
- 专用改价接口复用可选字段模型，缺少 `price` 或传 `null` 时的处理待完善。
- 已借出禁止改价仅在专用改价接口中执行，通用 PATCH 尚未统一执行该规则。
- 重复图书检查在新增接口完成，数据库尚无书名与作者的唯一约束，修改时也未统一检查。
- 图书查询、新增和专用改价响应中的 `Book` 不含数据库 ID，客户端获取 ID 的方式待完善。
- 命令行输入解析中，未借出分支误写为 `borrowed == False`；CLI 删除使用的列表序号与数据库 ID 语义不一致，删除提示也可能引用未定义或旧的 `book`。
- 借书数据库函数的“记录不存在”分支将 `conn.close()` 误写为 `conn.close`，连接关闭待修复。

现有测试未覆盖上述所有问题；测试通过仅说明已有用例通过。命令行入口暂不作为完整可用的演示流程。

## 后续路线

1. Docker 最小概念与 PostgreSQL 开发环境。
2. SQLAlchemy 模型、Session、事务与 CRUD 迁移。
3. 独立 ORM 测试库、Alembic 数据库迁移。
4. 注册登录、鉴权与资源归属校验。
5. 环境配置、日志、Docker Compose、CI 和完整运行说明。

当前项目仍使用 SQLite，上述工程化能力为后续计划，尚未实现。

# Library Book API

基于 FastAPI、SQLAlchemy 和 PostgreSQL 开发的图书借阅 API。

## 功能

- 图书增删改查
- 用户注册与密码哈希
- JWT 登录认证
- 图书借阅与归还
- 用户只能查看自己的借阅记录
- Alembic 数据库迁移
- pytest 接口测试
- Docker Compose 一键启动
- GitHub Actions 自动测试

## 技术栈

- Python 3.12
- FastAPI
- SQLAlchemy
- PostgreSQL
- Alembic
- pytest
- Docker Compose
- GitHub Actions

## 使用 Docker Compose 启动

### 1. 准备环境变量

复制示例配置：

```bash
cp .env.example .env