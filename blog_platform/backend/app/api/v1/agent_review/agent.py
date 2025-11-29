from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from backend.app.schemas.agent_review import (
    ReviewSessionCreate,
    ReviewDetailOut,
    ReviewSessionOut,
    ApplyRevisionIn,
)
from backend.app.crud.agent_review import get_review_session, apply_revision_to_blog
from backend.app.service.agent_review_service import (
    run_review_for_post,
    run_rewrite_for_post,
    run_style_check_for_post,
)
from backend.app.api.jwt import get_current_user
from backend.app.models.user import User
from backend.app.common.response.response_schema import response_base

review = APIRouter()


@review.post("/posts/{post_id}", summary="创建审稿会话")
async def create_review(
    post_id: int,
    body: ReviewSessionCreate,
    user: User = Depends(get_current_user),
):
    # 使用当前登录用户作为发起审稿的用户
    result = await run_review_for_post(
        post_id=post_id,
        user_id=user.id,
    )
    session = result["session"]
    review_result = result["result"]

    detail = ReviewDetailOut(
        session=ReviewSessionOut.from_orm(session),
        result=None
        if review_result is None
        else {
            "session_id": review_result.session_id,
            "issue_summary": review_result.issue_summary,
            "technical_issues": review_result.technical_issues,
            "style_issues": review_result.style_issues,
            "suggested_revision": review_result.suggested_revision,
            "diff_view": review_result.diff_view,
            "created_time": review_result.created_time,
        },
    )

    return response_base.response_200(
        msg="创建审稿会话成功",
        data=detail,
    )


@review.get("/sessions/{session_id}", summary="获取审稿会话详情")
async def get_review_detail(session_id: int):
    session = await get_review_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="审稿会话不存在")

    result = getattr(session, "result", None)

    detail = ReviewDetailOut(
        session=ReviewSessionOut.from_orm(session),
        result=None
        if not result
        else {
            "session_id": session.id,
            "issue_summary": result.issue_summary,
            "technical_issues": result.technical_issues,
            "style_issues": result.style_issues,
            "suggested_revision": result.suggested_revision,
            "diff_view": result.diff_view,
            "created_time": result.created_time.isoformat(),
        },
    )

    return response_base.response_200(
        msg="获取审稿会话详情成功",
        data=detail,
    )


@review.post("/sessions/{session_id}/apply", summary="应用审稿修改到博客")
async def apply_revision(session_id: int, body: ApplyRevisionIn):

    session = await get_review_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="审稿会话不存在")
    if session.status != 1:
        raise HTTPException(status_code=400, detail="审稿未完成，不能应用修改")

    result = getattr(session, "result", None)
    if not result or not result.suggested_revision:
        raise HTTPException(status_code=400, detail="没有可用的建议修改内容")

    new_content = body.override_content or result.suggested_revision
    blog = await apply_revision_to_blog(session, new_content=new_content)

    return response_base.response_200(
        msg="应用审稿修改成功",
        data={
            "blog_id": blog.id,
            "updated": True,
        },
    )


@review.post("/posts/{post_id}/rewrite", summary="直接改写博客内容（不创建会话）")
async def rewrite_post(post_id: int, user: User = Depends(get_current_user)):
    """直接对指定博客做一次改写，不创建审稿会话，只返回改写结果。"""
    result = await run_rewrite_for_post(post_id=post_id)
    return response_base.response_200(
        msg="改写博客成功",
        data={
            "post_id": post_id,
            "suggested_revision": result["suggested_revision"],
            "diff_view": result["diff_view"],
        },
    )


@review.post("/posts/{post_id}/style_check", summary="直接风格检查（不创建会话）")
async def style_check_post(post_id: int, user: User = Depends(get_current_user)):
    """直接对指定博客做一次风格检查，不创建审稿会话，只返回风格报告。"""
    result = await run_style_check_for_post(post_id=post_id)

    return response_base.response_200(
        msg="风格检查成功",
        data={
            "post_id": post_id,
            "style_issues": result["style_issues"],
        },
    )