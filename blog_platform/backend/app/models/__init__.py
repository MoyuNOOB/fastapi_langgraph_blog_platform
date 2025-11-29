#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from backend.app.models import user
from backend.app.models import blog
from backend.app.models import agent_review

# 新增model后，在list引入文件，而不是model类
models = [user, blog,agent_review]
