#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from functools import lru_cache

from pydantic import BaseSettings


class Settings(BaseSettings):
    """ 配置类 """

    # FastAPI
    TITLE: str = 'FastAPI'
    VERSION: str = 'v0.0.1'
    DESCRIPTION: str = """
fastapi_tortoise_mysql. 🚀

点击跳转 -> [master](https://gitee.com/wu_cl/fastapi_tortoise_mysql)
"""
    DOCS_URL: str = '/v1/docs'
    OPENAPI_URL: str = '/v1/openapi'
    REDOCS_URL: str = None

    # 静态文件代理
    STATIC_FILE: bool = True

    # Uvicorn
    UVICORN_HOST: str = '127.0.0.1'
    UVICORN_PORT: int = 8000
    UVICORN_RELOAD: bool = True

    # DB
    DB_ADD_EXCEPTION_HANDLERS: bool = False  # 线上环境请使用 False
    DB_AUTO_GENERATE_SCHEMAS: bool = True  # 线上环境请使用 False
    DB_ECHO: bool = False  # 是否显示SQL语句
    DB_HOST: str = '127.0.0.1'
    DB_PORT: int = 3306
    DB_USER: str = 'root'
    DB_PASSWORD: str = '123456'
    DB_DATABASE: str = 'ftm'
    DB_ENCODING: str = 'utf8mb4'

    # Redis
    REDIS_HOST: str = '127.0.0.1'
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ''
    REDIS_DATABASE: int = 0
    REDIS_TIMEOUT: int = 10
    REDIS_EXPIRE_TIME: int = 300  # 过期时间5分钟

    # MQ
    MQ_HOST: str = '127.0.0.1'
    MQ_PORT: int = 5672
    MQ_USER: str = 'ftm_user'
    MQ_PASSWORD: str = 'ftm_password'
    MQ_VHOST: str = '/ftm'
    MQ_TIMEOUT: int = 10
    MQ_EXPIRE_TIME: int = 300  # 过期时间5分钟

    # Captcha
    CAPTCHA_EXPIRATION_TIME: int = 60 * 2  # 单位：s

    # Token
    TOKEN_ALGORITHM: str = 'HS256'
    TOKEN_SECRET_KEY: str = '0ou59yzj-QwX8JT8Mq8o2rIOvxpwtVWH3aFH2-QLo7c'  # 密钥 secrets.token_urlsafe(32))
    TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 3  # 单位：m

    # Email
    EMAIL_DESCRIPTION: str = 'fastapi_tortoise_mysql'  # 默认发件说明
    EMAIL_SERVER: str = 'smtp.qq.com'
    EMAIL_PORT: int = 465
    EMAIL_USER: str = 'xxxxx-nav@qq.com'
    EMAIL_PASSWORD: str = 'hahahalueluelue'  # 授权密码，非邮箱密码
    EMAIL_SSL: bool = True  # 是否使用ssl

    # Cookies
    COOKIES_MAX_AGE: int = 60 * 5  # 单位：s

    # 中间件
    MIDDLEWARE_CORS: bool = True
    MIDDLEWARE_GZIP: bool = True
    MIDDLEWARE_ACCESS: bool = True
    MIDDLEWARE_TIMING: bool = True


@lru_cache
def get_settings():
    """ 读取配置优化写法 """
    return Settings()


settings = get_settings()
