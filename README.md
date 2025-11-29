# Blog Platform 

一个基于 FastAPI 的博客平台，集成了使用 LangGraph + 大模型的智能审稿 Multi-Agent 微服务。

- 主项目：`blog_platform/backend`（Pydantic V1)
- 审稿微服务：`agent_service`（Pydantic v2 + langgraph + langchain）

---

## 1. 功能概要

### 1.1 博客平台（`blog_platform/backend`）

- 用户登录 / JWT 鉴权
- 博客 CRUD
  - 创建博客（异步任务入队）
  - 获取全站博客列表
  - 获取当前用户博客列表
  - 获取博客详情
  - 更新 / 删除博客
- 审稿会话管理
  - 创建审稿会话（基于指定博客）
  - 查询审稿会话详情
  - 应用审稿建议更新博客内容

### 1.2 审稿 Agent 微服务（`agent_service`）

基于 `langgraph` + `langchain_openai.ChatOpenAI` + DashScope OpenAI 接口，构建多节点审稿工作流：

- 技术审稿：识别技术错误 / 风险
- 风格分析：分析语言、技术栈、内容性质等
- 问题汇总：给出整体问题概览
- 改写：生成修改后的完整文章

对外暴露 3 个 HTTP 接口：

- `POST /review`：完整审稿（技术 + 风格 + 汇总 + 改写）
- `POST /rewrite`：只做改写
- `POST /style_check`：只做风格检查

---

## 2. 环境准备

主项目用的是v1的pydantic，微服务用的是v2的pydantic，建议使用 Conda 管理不同环境，主项目和微服务分别一个环境

### 2.1 克隆仓库

```bash
git clone <your-repo-url> FastapiDemo
cd FastapiDemo
```

### 2.2 安装依赖
假设分别为env1和env2
```bash
#安装微服务依赖
cd agent_service
conda activate env1 
pip install -r requirements.txt
#安装主项目依赖
cd blog_platform/backend
conda activate env2 
pip install -r requirements.txt
```