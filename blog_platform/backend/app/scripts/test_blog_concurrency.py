#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import time
from typing import List

import pytest
import httpx


# ================================
# 配置区：根据自己环境调整
# ================================
BASE_URL = "http://127.0.0.1:8000"  # 你的 uvicorn 地址
API_PREFIX = "/v1/blog"             # 全局路由前缀
ACCESS_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIxMzcwNTg5MjUsInN1YiI6IjIifQ.Mgfr4bdipgUE6B9CLReldUR4KSHVkwF12Rtnl2p_uDo"  # TODO: 替换成你自己的 JWT


# 并发参数
WRITE_CONCURRENCY = 50   # 并发写任务数
READ_CONCURRENCY = 100   # 并发读任务数
WAIT_FOR_MQ_SECONDS = 2  # 写入后等待 MQ 消费的时间，视环境可调


def _auth_headers() -> dict:
    """生成带 JWT 的请求头"""
    return {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }


@pytest.mark.asyncio
async def test_high_concurrency_create_and_read():
    """
    高并发场景下：
    1. 并发创建多篇博客（写请求 -> 走 MQ）
    2. 等待 MQ 消费完成
    3. 并发读取“我的博客列表”和部分博客详情
    """

    if ACCESS_TOKEN == "PUT_YOUR_JWT_HERE":
        pytest.skip("请先在脚本顶部配置 ACCESS_TOKEN 再运行此测试")

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=10) as client:

        # ============ 1. 并发创建博客（写） ============
        async def create_post_task(i: int):
            payload = {
                "title": f"concurrent-title-{i}",
                "content": f"concurrent-content-{i}",
            }
            resp = await client.post(
                f"{API_PREFIX}/posts",
                json=payload,
                headers=_auth_headers(),
            )
            return resp.status_code, resp.json()

        write_tasks = [create_post_task(i) for i in range(WRITE_CONCURRENCY)]

        t0 = time.perf_counter()
        write_results: List[tuple] = await asyncio.gather(*write_tasks)
        t1 = time.perf_counter()

        ok_count = sum(1 for code, _ in write_results if code == 200)
        print(f"[WRITE] 并发创建 {WRITE_CONCURRENCY} 篇博客，用时 {t1 - t0:.2f}s，成功 {ok_count}")

        # 断言：至少大部分写入请求成功（根据需要调整阈值）
        assert ok_count >= WRITE_CONCURRENCY * 0.9

        # ============ 2. 等待 MQ worker 消费 ============
        # 根据你的 MQ / DB 性能调整等待时间；只是为了让后面的读能看到新数据
        await asyncio.sleep(WAIT_FOR_MQ_SECONDS)

        # ============ 3. 并发读取“我的博客列表” ============
        async def read_my_posts_task():
            resp = await client.get(
                f"{API_PREFIX}/posts/my",
                headers=_auth_headers(),
            )
            return resp.status_code, resp.json()

        read_list_tasks = [read_my_posts_task() for _ in range(READ_CONCURRENCY)]

        t2 = time.perf_counter()
        read_list_results: List[tuple] = await asyncio.gather(*read_list_tasks)
        t3 = time.perf_counter()

        ok_read_list = sum(1 for code, _ in read_list_results if code == 200)
        print(f"[READ-LIST] 并发读取 my posts {READ_CONCURRENCY} 次，用时 {t3 - t2:.2f}s，成功 {ok_read_list}")

        assert ok_read_list == READ_CONCURRENCY

        # 从其中一个列表响应里，取一些 blog_id 用来测详情
        sample_data = None
        for code, body in read_list_results:
            if code == 200 and isinstance(body, dict) and "data" in body:
                if isinstance(body["data"], list) and body["data"]:
                    sample_data = body["data"]
                    break

        if not sample_data:
            pytest.skip("my posts 列表为空，无法做详情并发测试")

        # 取前 N 个 blog_id 做详情请求
        detail_ids = [item["id"] for item in sample_data[:10] if "id" in item]

        async def read_detail_task(blog_id: int):
            resp = await client.get(
                f"{API_PREFIX}/posts/{blog_id}",
                headers=_auth_headers(),
            )
            return resp.status_code, resp.json()

        detail_tasks = [read_detail_task(bid) for bid in detail_ids for _ in range(10)]
        # 上面等价于：每个 blog_id 读 10 次，合计 10 * len(detail_ids) 个详情请求

        t4 = time.perf_counter()
        detail_results: List[tuple] = await asyncio.gather(*detail_tasks)
        t5 = time.perf_counter()

        ok_detail = sum(1 for code, _ in detail_results if code == 200)
        print(f"[READ-DETAIL] 并发读取详情 {len(detail_tasks)} 次，用时 {t5 - t4:.2f}s，成功 {ok_detail}")

        assert ok_detail == len(detail_tasks)