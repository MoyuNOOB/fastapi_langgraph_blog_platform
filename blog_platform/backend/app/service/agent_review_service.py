from typing import Optional, Dict, Any

from backend.app.crud.agent_review import create_review_session, save_review_result, mark_session_failed
from backend.app.models.blog import Blog
import httpx

# 审稿服务，调用agent微服务
async def run_review_for_post(
    post_id: int,
    user_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    入口：对指定 post_id 做一次审稿，返回完整结果（给 API 用）
    """
    # 创建会话
    session = await create_review_session(post_id=post_id, user_id=user_id)
    try:
        # 读博客内容
        blog = await Blog.get(id=post_id)
        # 调用 agent微服务
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
            resp = await client.post(
                "http://127.0.0.1:9000/review",
                json={
                    "title": blog.title,
                    "content": blog.content,
                },
            )
        resp.raise_for_status()
        data = resp.json()  # 这里就是 AgentState 的字典

        # 4. 从返回中取出各字段
        technical_issues = data.get("technical_issues", "")
        style_issues = data.get("style_issues", "")
        issue_summary = data.get("summary", "")
        suggested_revision = data.get("rewritten_text", "")
        diff_view = data.get("diff", "")

        # 5. 保存结果到你原有的 result 表
        result = await save_review_result(
            session=session,
            issue_summary=issue_summary,
            technical_issues=technical_issues,
            style_issues=style_issues,
            suggested_revision=suggested_revision,
            diff_view=diff_view,
        )

        return {
            "session": session,
            "result": result,
        }

    except Exception:
        await mark_session_failed(session)
        raise

#新增直接调用改写功能和风格分析汇总功能的服务
async def run_rewrite_for_post(post_id: int) -> Dict[str, Any]:
    """
    调用agent微服务直接对指定 post_id 做一次改写，返回完整结果（给 API 用）
    """
    blog = await Blog.get(id=post_id)

    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        resp = await client.post(
            "http://127.0.0.1:9000/rewrite",
            json={
                "title": blog.title,
                "content": blog.content,
            },
        )
    resp.raise_for_status()
    data = resp.json()

    suggested_revision = data.get("rewritten_text", "")
    diff_view = data.get("diff", "")

    return {
        "suggested_revision": suggested_revision,
        "diff_view": diff_view,
    }

async def run_style_check_for_post(post_id: int) -> Dict[str, Any]:
    """
    调用agent微服务直接对指定 post_id 做一次风格检查，返回完整结果（给 API 用）
    """
    blog = await Blog.get(id=post_id)

    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        resp = await client.post(
            "http://127.0.0.1:9000/style_check",
            json={
                "title": blog.title,
                "content": blog.content,
            },
        )
    resp.raise_for_status()
    data = resp.json()

    style_issues = data.get("style_issues", "")

    return {
        "style_issues": style_issues,
    }