# 基于 fastapi_tortoise_mysql 的博客系统与大模型知识智能体设计文档

## 1. 现有后端架构概览

### 1.1 技术栈

- Web 框架：FastAPI
- ORM：Tortoise ORM（MySQL）
- 缓存 / KV：Redis（aioredis）
- 其他：
  - fastapi-pagination（分页）
  - passlib（密码加密）
  - jose（JWT）
  - pydantic（配置与 Schema）

### 1.2 目录结构（后端部分）

[backend/app](cci:7://file:///d:/FastapiDemo/fastapi_tortoise_mysql/backend/app:0:0-0:0) 关键目录与模块：

- **[main.py](cci:7://file:///d:/FastapiDemo/fastapi_tortoise_mysql/backend/app/main.py:0:0-0:0)**
  - 应用入口：
    - `app = register_app()`
    - 调用 uvicorn 启动（本地调试模式）
  - 示例根路由 `@app.get('/')` 用于健康检查 / Hello World

- **`api/registrar.py`**（应用装配核心）
  - `register_app()`：
    - 创建 `FastAPI` 实例（标题、版本、docs 路径等来自 `settings`）
    - 调用以下注册函数：
      - `register_static_file(app)`：挂载 `/static`
      - `register_middleware(app)`：注册中间件
      - `register_router(app)`：注册业务路由（`v1`）
      - `register_db(app)`：注册 Tortoise / MySQL
      - `register_init(app)`：应用启动/关闭时连接/关闭 Redis
      - `register_page(app)`：启用分页
      - `register_exception(app)`：注册全局异常处理

- **`api/router.py`**（API 路由总入口）
  - 定义 `v1 = APIRouter(prefix='/v1')`
  - include：
    - `/captcha` 图形验证码
    - `/users` 用户相关接口

- **`api/v1/auth/user.py`**（用户认证与管理）
  - 核心接口：
    - `POST /v1/users/login`：表单登录（使用 OAuth2PasswordRequestForm）
    - `POST /v1/users/logout`：登出
    - `POST /v1/users/register`：注册
    - 密码重置、获取用户信息、更新信息、头像上传/删除等
  - 依赖：
    - `backend.app.api.jwt`：token 校验、当前用户依赖
    - `backend.app.api.service.user_service`：业务逻辑
    - `backend.app.crud.crud_user`：数据库操作
    - `backend.app.schemas.*`：输入输出 Schema

- **`api/v1/verify/captcha.py`**（验证码服务）
  - `GET /v1/captcha`：生成图片验证码，写入 Redis，返回图片流
  - `GET /v1/captcha/test`：用于调试

- **[models/](cci:7://file:///d:/FastapiDemo/fastapi_tortoise_mysql/backend/app/models:0:0-0:0)**（Tortoise ORM 模型）
  - `user.py`：`User` 表
    - 字段：`id`, `uid`, `username`, `password`, `email`, `is_superuser`, 时间戳等
    - `Meta.table = 'user'`
  - [__init__.py](cci:7://file:///d:/FastapiDemo/fastapi_tortoise_mysql/backend/app/__init__.py:0:0-0:0)：
    - 引入所有 model 模块
    - 暴露 `models = [user, ...]` 供 DB 配置使用

- **`database/db_mysql.py`**（MySQL 配置与集成）
  - `db_config`：
    - `connections.default`：MySQL 连接参数（host/port/user/password/database/charset）
    - `apps.models`：模型列表来自 `backend.app.models.models`
  - `register_db(app)`：
    - `register_tortoise(app, config=db_config, generate_schemas=..., add_exception_handlers=...)`

- **`common/redis.py`**（Redis 封装）
  - `class RedisCli(Redis)`：
    - 从 `settings` 中读取 host/port/password/db 等
    - `init_redis_connect()`：在应用启动阶段 `ping()` 检查 Redis 连通性；失败则日志 + `sys.exit()`
  - `redis_client = RedisCli()`：全局单例，供其他模块使用

- **[core/conf.py](cci:7://file:///d:/FastapiDemo/fastapi_tortoise_mysql/backend/app/core/conf.py:0:0-0:0)**（配置中心）
  - `Settings(BaseSettings)`：
    - FastAPI 基础配置（TITLE、VERSION、DOCS_URL 等）
    - DB 配置（`DB_HOST`、`DB_DATABASE` 等）
    - Redis 配置（`REDIS_HOST`、`REDIS_PORT` 等）
    - Token 配置（算法、密钥、过期时间）
    - 中间件开关等

- **[init_test_data.py](cci:7://file:///d:/FastapiDemo/fastapi_tortoise_mysql/backend/app/init_test_data.py:0:0-0:0)**
  - 用于命令行创建初始超级用户
  - 直接通过 `Tortoise.init(config=db_config)` 与 `User.create(...)` 操作数据库

整体调用链整理为：

> main.py → register_app() → 注册路由、DB、Redis 等 → 接口层(api) → service 层 → crud / model 层 → MySQL + Redis

---

## 2. Redis 与 MySQL 使用方式

### 2.1 MySQL（Tortoise ORM）

- **配置**：在 `db_mysql.py` 中构造 `db_config`，在 `registrar.py` 中通过 `register_db(app)` 注册。
- **模型定义**：在 [models](cci:7://file:///d:/FastapiDemo/fastapi_tortoise_mysql/backend/app/models:0:0-0:0) 目录中定义各个 `Model`，通过 `models/__init__.py` 统一导入。
- **访问模式**：
  - `crud_xxx.py`：集中封装数据库访问（`create`, `get`, `update`, `delete`, `filter` 等）
  - `api/service/xxx_service.py`：编写业务逻辑，调用 CRUD
  - `api/v1/...`：HTTP 接口，仅做参数接收与调用 service，返回统一响应

### 2.2 Redis

- **配置**：在 [core/conf.py](cci:7://file:///d:/FastapiDemo/fastapi_tortoise_mysql/backend/app/core/conf.py:0:0-0:0) 通过 `REDIS_HOST`/`REDIS_PORT` 等配置。
- **连接与生命周期**：
  - 应用启动时：`startup_event` 调用 `await redis_client.init_redis_connect()`
  - 应用关闭时：`await redis_client.close()`
- **使用示例**：验证码
  - 生成验证码时：`await redis_client.set(uid, code, expire_time)`
  - 校验验证码时：`await redis_client.get(uid)` 比较是否一致

后续可用于：

- 缓存热门数据、会话信息
- 接口限流
- 文章浏览量计数等

---

## 3. 博客模块设计

### 3.1 功能需求

- 博客文章管理：
  - 创建、编辑、删除文章
  - 文章列表、详情查询
  - 支持分类与标签
- 评论系统（可选）：
  - 对文章进行评论
  - 查看评论列表
- 权限：
  - 登录用户新建/修改/删除自己的文章
  - 超级管理员可以管理所有文章和评论
  - 未登录用户只能查看文章和评论

### 3.2 数据库模型设计（Tortoise）

新建文件 `backend/app/models/blog.py`，示意结构：

- **Category**
  - `id`, `name`, `description`, `created_time`, `updated_time`
- **Tag**
  - `id`, `name`, `created_time`
- **Post**
  - `id`
  - `title`
  - `summary`
  - `content`
  - `author`（ForeignKey 到 `User`）
  - `category`（ForeignKey 到 `Category`）
  - `tags`（ManyToMany 到 `Tag`）
  - `is_published`（bool）
  - `view_count`（int，可选，实际统计可放 Redis）
  - `created_time`, `updated_time`
- **Comment**（可选）
  - `id`
  - `post`（FK 到 `Post`）
  - `user`（FK 到 `User`，也可以允许匿名）
  - `content`
  - `created_time`

再在 `backend/app/models/__init__.py` 中增加：

```python
from backend.app.models import user, blog

models = [user, blog]
```

### 3.3 Schemas 设计（Pydantic）

新建 `backend/app/schemas/blog.py`：

- 请求模型：
  - `CreatePost`：标题、内容、分类 ID、标签 ID 列表、是否发布等
  - `UpdatePost`：可选字段（标题、内容等）
  - `CreateComment`：文章 ID、内容
- 响应模型：
  - `PostBase`：通用字段
  - `PostDetail`：包含作者、分类、标签、评论列表
  - `PostListItem`：列表优化字段（如摘要、发布时间等）
  - `CommentInfo`：评论详情

### 3.4 CRUD 与 Service

- 新建 `backend/app/crud/crud_blog.py`：
  - `create_post`, `update_post`, `delete_post`
  - `get_post_by_id`, `get_post_list`（支持分页、条件过滤）
  - `create_comment`, `get_comments_by_post` 等
- 新建 `backend/app/api/service/blog_service.py`：
  - 衔接 `User` 与 `Post`（设置 author）
  - 权限判断：当前用户是否为作者 / 管理员
  - 复杂业务逻辑封装（比如发布前检查）

### 3.5 API 路由设计

新建 `backend/app/api/v1/blog/post.py`（或 `blog.py`）：

- `blog = APIRouter()`
- 路由示例：
  - `POST /v1/blog/posts`：创建文章（`Depends(jwt.get_current_user)`）
  - `GET /v1/blog/posts`：分页获取文章列表
  - `GET /v1/blog/posts/{post_id}`：文章详情
  - `PUT /v1/blog/posts/{post_id}`：更新文章（作者或管理员）
  - `DELETE /v1/blog/posts/{post_id}`：删除文章（作者或管理员）
  - `POST /v1/blog/posts/{post_id}/comments`：添加评论
  - `GET /v1/blog/posts/{post_id}/comments`：获取评论列表

在 `backend/app/api/router.py` 中挂载：

```python
from backend.app.api.v1.blog.post import blog

v1.include_router(blog, prefix='/blog', tags=['博客'])
```

### 3.6 Redis 在博客中的应用（可选增强）

- **浏览量统计**：
  - 每次访问文章详情：`INCR post:view:{post_id}`
  - 定时任务或触发条件下，回写 MySQL
- **热门文章缓存**：
  - 在 Redis 中维护 topN 列表，提高首页/侧边栏访问性能
- **评论限流**：
  - 使用 Redis 记录用户评论频率，简单实现反刷机制

---

## 4. 大模型开发知识智能体设计

### 4.1 整体目标

在现有博客系统和用户体系基础上，构建一个「开发知识智能体」：

- 知识来源：你写在博客里的技术文章 / 笔记（后续可扩展到项目文档、API 等）
- 功能：
  - 用户提出技术问题，系统基于已存在的博客内容进行检索和回答
  - 支持会话式问答（上下文记忆）

### 4.2 知识库与向量化

#### 4.2.1 知识来源

- 数据源：博客文章 `Post`：
  - 使用 `title + summary + content` 作为基础文本
- 后续扩展：
  - 项目 README、设计文档
  - API 文档（OpenAPI schema 中的描述信息）

#### 4.2.2 知识向量化与存储

新建一个模型（如 `backend/app/models/knowledge.py`）：

- `KnowledgeChunk`
  - `id`
  - `post`（FK 到 `Post`）
  - `chunk_index`
  - `content`（文本片段）
  - `embedding`（向量，保存为 JSON 或 BLOB）
  - `created_time`

流程：

1. **离线/脚本**：
   - 遍历所有已发布文章
   - 按一定规则将正文按段拆分（chunk）
   - 调用外部 Embedding API（如 OpenAI Embeddings）
   - 将 `content + embedding` 存入 `KnowledgeChunk`
2. **在线检索**：
   - 接收到用户问题 → 调用相同 Embedding API 得到 query 向量
   - 在 `KnowledgeChunk` 中做相似度计算（初期可以 Python 读取进内存计算，量大时使用向量库如 Qdrant 等）
   - 选取 Top-K 片段作为上下文提供给大模型

### 4.3 大模型调用封装

增加一个 LLM 客户端模块，如 `backend/app/common/llm_client.py`：

- 从环境变量或配置中读取：
  - `LLM_API_BASE`
  - `LLM_API_KEY`
  - 默认模型名等
- 暴露函数：
  - `async def chat_with_context(question: str, context_chunks: List[str], history: List[Message]) -> str`

注意：

- 不要把 API Key 写死在代码，读取环境变量或配置文件。
- 做超时与异常处理。

### 4.4 智能体 API 设计

新建 `backend/app/api/v1/agent/assistant.py`：

- `agent = APIRouter()`

核心接口：

- `POST /v1/agent/query`
  - 请求体示例：
    ```json
    {
      "question": "如何在这个项目里新增一个博客接口？",
      "session_id": "optional"
    }
    ```
  - 依赖：
    - `current_user: User = Depends(jwt.get_current_user)`（需要登录）
  - 处理流程：
    1. 对 `question` 做向量化
    2. 检索 `KnowledgeChunk`，得到相关片段
    3. 如果有 `session_id`，读取最近 N 条对话历史（可从 MySQL 或 Redis）
    4. 组装 prompt（系统指令 + 上下文片段 + 历史 + 当前问题）
    5. 调用 LLM Client 获取回答
    6. 返回回答，并记录本轮问答（用于会话上下文）

可以选择：

- 会话存储在 MySQL：
  - `Conversation` + `Message` 表
- 或简单放在 Redis：
  - key: `chat:{user_id}:{session_id}` → list of messages

在 `api/router.py` 中挂载：

```python
from backend.app.api.v1.agent.assistant import agent
v1.include_router(agent, prefix='/agent', tags=['智能体'])
```

### 4.5 权限与限流

- 权限：
  - 所有智能体接口 `Depends(jwt.get_current_user)` 保证用户登录
  - 可以对 `is_superuser` 用户开放部分管理类能力（未来再扩展）
- 限流（基于 Redis）：
  - 对每个 user_id 做简单的计数限制：
    - key: `rate:agent:{user_id}:{date}`
    - 超过配额（如每天 N 次）则返回提示

---

## 5. 实施步骤建议

建议按以下顺序实施，每一步都可单独调试：

1. **博客模型与接口**
   - 定义 `Category`/`Tag`/`Post`/`Comment` 模型
   - 更新 `models/__init__.py`
   - 编写 `schemas/blog.py`
   - 编写 `crud_blog.py` 与 `blog_service.py`
   - 编写 `api/v1/blog` 路由并挂载

2. **完善博客与用户权限关系**
   - 路由中引入 [jwt.get_current_user](cci:1://file:///d:/FastapiDemo/fastapi_tortoise_mysql/backend/app/api/jwt.py:61:0-78:15)
   - 校验文章作者 / 管理员权限

3. **（可选）引入 Redis 做浏览量与缓存**

4. **知识库与向量化**
   - 定义 `KnowledgeChunk` 模型
   - 编写初始化脚本：从 `Post` 导出 chunk + 调用 Embedding API + 写入 DB

5. **大模型客户端封装**
   - 实现 `llm_client.py`
   - 测试基础的问答功能

6. **智能体 API**
   - 实现 `/v1/agent/query`
   - 结合检索 + LLM + 会话历史进行回答
   - 增加权限与 Redis 限流

---

