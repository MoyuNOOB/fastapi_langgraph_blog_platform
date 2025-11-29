#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os,sys
import random
import string

import pytest
from tortoise import Tortoise

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from backend.app.database.db_mysql import db_config
from backend.app.models.user import User
from backend.app.models.blog import Blog
from backend.app.api import jwt


def random_str(length: int) -> str:
    """
    生成指定长度的随机字符串（字母+数字）
    """
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))


async def init_db():
    """
    使用项目现有的 db_config 初始化 Tortoise 连接。
    假设表结构已经建好（通过 aerich 或自动建表）。
    """
    await Tortoise.init(config=db_config)
    # 如需自动建表，可临时打开下一行
    # await Tortoise.generate_schemas()


async def create_test_users(num_users: int = 10):
    """
    创建测试用户，返回创建成功的用户列表
    """
    users = []
    password_plain = "test123"
    password_hashed = jwt.get_hash_password(password_plain)

    for _ in range(num_users):
        username = f"testuser_{random_str(6)}"
        email = f"{random_str(6)}@example.com"

        user = await User.create(
            username=username,
            email=email,
            password=password_hashed,
        )
        users.append(user)

    return users


async def create_test_blogs_for_users(users, min_per_user: int = 20, max_per_user: int = 50):
    """
    为每个用户创建随机数量的博客（20-50 条）
    """
    for user in users:
        blog_count = random.randint(min_per_user, max_per_user)
        print(f"用户 {user.id} / {user.username} 生成 {blog_count} 条博客")

        for _ in range(blog_count):
            title_len = random.randint(5, 20)
            content_len = random.randint(10, 50)

            title = random_str(title_len)
            content = random_str(content_len)

            await Blog.create(
                user_id=user.id,
                user_name=user.username,
                title=title,
                content=content,
            )


@pytest.mark.asyncio
async def test_generate_test_data():
    """
    使用 pytest 生成测试用户和博客数据。
    跑一次就插一次数据，注意不要在生产库里执行。
    """
    await init_db()
    print("开始创建测试用户...")
    users = await create_test_users(10)
    print("测试用户创建完成：")
    for u in users:
        print(f"  id={u.id}, username={u.username}, email={u.email}")

    print("开始为用户生成测试博客...")
    await create_test_blogs_for_users(users)
    print("测试博客生成完成。")

    # 简单断言：至少有 10 个用户、每个用户至少 20 篇博客
    assert len(users) == 10
    for u in users:
        count = await Blog.filter(user_id=u.id).count()
        assert count >= 20

    await Tortoise.close_connections()