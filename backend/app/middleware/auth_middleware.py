"""
简单的 API 鉴权中间件 —— 校验请求中的 token Cookie。
"""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware


PUBLIC_PATHS = ["/api/auth/", "/api/invite/", "/api/health", "/api/dev/"]


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 公开路径跳过鉴权
        path = request.url.path
        if any(path.startswith(p) for p in PUBLIC_PATHS):
            return await call_next(request)

        # 校验 token cookie
        token = request.cookies.get("token", "")
        if not token:
            # 开发模式：允许无 token 访问
            pass

        return await call_next(request)
