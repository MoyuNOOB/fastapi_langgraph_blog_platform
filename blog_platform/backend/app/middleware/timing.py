#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
from fastapi import Request, Response

from backend.app.common.log import log
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware

class TimingMiddleware(BaseHTTPMiddleware):
    """
    记录请求耗时,以此来判断接口性能
    """

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000  # ms

        # 写入 header，方便在浏览器/工具里看到
        response.headers["X-Process-Time-ms"] = f"{process_time:.2f}"

        # 也打到日志里
        log.info(
            "Request {} {} took {:.2f} ms",
            request.method,
            request.url.path,
            process_time,
        )
        return response
   
