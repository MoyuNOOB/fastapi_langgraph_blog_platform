#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from fastapi import FastAPI
from pydantic import BaseModel
from agent_graph import build_agent_graph, AgentState,rewrite_and_diff_node,check_style_node

app = FastAPI(title="Agent Review Service (Pydantic v2)")

graph = build_agent_graph()

class ReviewRequest(BaseModel):
    title: str
    content: str

@app.get('/')
async def root():
    return {"message": "A pydanticV2 agent service with langchain for blog review"}

@app.post("/review")
async def review_article(req: ReviewRequest):
    # 调用 langgraph 的异步接口
    result: AgentState = await graph.ainvoke(
        {"title": req.title, "content": req.content}
    )
    return result

@app.post("/rewrite")
async def rewrite_article(req: ReviewRequest):
    """
    只做改写：调用 rewrite_and_diff_node，返回改写后的文本（以及 diff，如果有）。
    """
    state: AgentState = {
        "title": req.title,
        "content": req.content,
    }
    new_state = await rewrite_and_diff_node(state)

    return {
        "rewritten_text": new_state.get("rewritten_text", ""),
        "diff": new_state.get("diff", ""),
    }


@app.post("/style_check")
async def style_check_article(req: ReviewRequest):
    """
    只做风格检查：调用 check_style_node，返回风格问题报告。
    """
    state: AgentState = {
        "title": req.title,
        "content": req.content,
    }
    new_state = await check_style_node(state)

    return {
        "style_issues": new_state.get("style_issues", ""),
    }