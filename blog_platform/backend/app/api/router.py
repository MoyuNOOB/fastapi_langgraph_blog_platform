#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from fastapi import APIRouter

from backend.app.api.v1.auth.user import user
from backend.app.api.v1.verify.captcha import captcha
from backend.app.api.v1.blog.post import blog
from backend.app.api.v1.agent_review.agent import review

v1 = APIRouter(prefix='/v1')

v1.include_router(captcha, prefix='/captcha', tags=['图形验证码'])

v1.include_router(user, prefix='/users', tags=['用户'])

v1.include_router(blog, prefix='/blog', tags=['博客'])

v1.include_router(review, prefix='/review', tags=['审稿'])