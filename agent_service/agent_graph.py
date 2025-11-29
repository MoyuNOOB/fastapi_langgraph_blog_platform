from typing import TypedDict,Optional
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from prompts import (
    technical_prompt,
    style_prompt,
    summary_prompt,
    rewrite_prompt,
)

import os
from dotenv import load_dotenv

load_dotenv()  #自动加载当前目录下的 .env

"""封装数据类型"""
class AgentState(TypedDict):
    title: str
    content: str
    technical_issues: Optional[str] = None
    style_issues: Optional[str] = None
    summary: Optional[str] = None
    technical_passed: Optional[bool] = None
    rewritten_text: Optional[str] = None
    diff: Optional[str] = None


"""封装异步 LLM 客户端，供各个节点复用。"""
async def get_llm() -> ChatOpenAI:
    return  ChatOpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        model="qwen-plus",
    )

"""技术审稿节点：生成技术审稿报告，并解析最终结论设置 technical_passed。"""
async def review_techical_node(state: AgentState) -> AgentState:
    llm = await get_llm()
    prompt_value = await technical_prompt.ainvoke({
        "title": state["title"],
        "content": state["content"],
    })
    resp = await llm.ainvoke(prompt_value.to_messages())

    report = resp.content or ""
    state["technical_issues"] = report

    # 解析报告中最后输出的“最终结论：通过/不通过”，设置 technical_passed
    normalized = report.replace(" ", "")
    if "最终结论：通过" in normalized:
        state["technical_passed"] = True
    elif "最终结论：不通过" in normalized:
        state["technical_passed"] = False
    else:
        # 若未能解析出结论，默认视为不通过，避免误放行
        state["technical_passed"] = False

    return state

"""风格检查节点：在技术审稿通过后，对文章风格进行分析。"""
async def check_style_node(state: AgentState) -> AgentState:
    llm = await get_llm()
    prompt_value = await style_prompt.ainvoke({
        "title": state["title"],
        "content": state["content"],
    })
    resp = await llm.ainvoke(prompt_value.to_messages())
    state["style_issues"] = resp.content
    return state

"""汇总节点：根据技术审稿和风格审稿生成整体问题总结。"""
async def summarize_issues_node(state: AgentState) -> AgentState:
    llm = await get_llm()

    prompt_value = await summary_prompt.ainvoke({
        "technical": state.get("technical_issues", ""),
        "style": state.get("style_issues", ""),
    })
    resp = await llm.ainvoke(prompt_value.to_messages())

    state["summary"] = resp.content
    return state

"""改写节点：按需单独调用，不再自动挂在图中。"""
async def rewrite_and_diff_node(state: AgentState) -> AgentState:
    llm = await get_llm()
    prompt_value = await rewrite_prompt.ainvoke({
        "title": state["title"],
        "content": state["content"],
        "technical": state.get("technical_issues", ""),
        "style": state.get("style_issues", ""),
    })
    resp = await llm.ainvoke(prompt_value.to_messages())

    state["rewritten_text"] = resp.content
    return state

def route_after_technical(state: AgentState) -> str:
    """根据技术审稿结果决定后续流向。

    - 通过：返回 "pass"，进入风格检查
    - 不通过：返回 "fail"，直接 END，由前端决定是否调用改写
    """
    if state.get("technical_passed"):
        return "pass"
    return "fail"

def build_agent_graph() -> StateGraph:
    """构建审稿主流程：技术审稿 -> (通过) 风格检查 -> 汇总 -> END。"""
    workflow = StateGraph(AgentState)

    # 节点注册
    workflow.add_node("review_technical", review_techical_node)
    workflow.add_node("check_style", check_style_node)
    workflow.add_node("summarize_issues", summarize_issues_node)

    # 入口：先做技术审稿
    workflow.set_entry_point("review_technical")

    # 审稿后根据 technical_passed 走不同分支
    workflow.add_conditional_edges(
        "review_technical",
        route_after_technical,
        {
            "pass": "check_style",  # 通过 -> 风格检查
            "fail": END,              # 不通过 -> 直接结束
        },
    )

    # 通过后的直线路径：风格检查 -> 汇总 -> END
    workflow.add_edge("check_style", "summarize_issues")
    workflow.add_edge("summarize_issues", END)

    return workflow.compile()