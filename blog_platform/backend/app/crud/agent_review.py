
from typing import Optional
from tortoise.transactions import in_transaction
from backend.app.models.agent_review import PostReviewSession,PostReviewResult
from backend.app.models.blog import Blog


async def create_review_session(post_id:int,user_id:int,auto_apply:bool=False)->PostReviewSession:
    '''
    创建一条session记录，初始status为0(待处理)
    '''
    return await PostReviewSession.create(
        post_id=post_id,
        user_id=user_id,
        status=0,
        auto_apply=auto_apply
    )

async def get_review_session(session_id:int)->Optional[PostReviewSession]:
    '''
    通过session_id获取session,不存在返回None
    '''
    return await PostReviewSession.get_or_none(id=session_id).prefetch_related("result","post")

async def save_review_result(
    session: PostReviewSession,
    issue_summary: str,
    technical_issues: str,
    style_issues: str,
    suggested_revision: str,
    diff_view: str,
) -> PostReviewResult:
    '''
    会话处理完成后，保存review结果，同时更新session状态为1(已完成)
    '''
    async with in_transaction():
        result = await PostReviewResult.create(
            session=session,
            issue_summary=issue_summary,
            technical_issues=technical_issues,
            style_issues=style_issues,
            suggested_revision=suggested_revision,
            diff_view=diff_view,
        )
        session.status = 1
        await session.save()
    return result

async def mark_session_failed(session: PostReviewSession)->PostReviewSession:
    '''
    会话处理失败，更新session状态为2(失败)
    '''
    session.status = 2
    await session.save()
    return session

async def apply_revision_to_blog(session: PostReviewSession, new_content: str) -> Blog:
    '''
    应用修改到博客
    '''
    blog = await Blog.get(id=session.post_id)
    blog.content = new_content
    await blog.save()
    return blog