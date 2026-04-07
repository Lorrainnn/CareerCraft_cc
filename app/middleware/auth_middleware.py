from jose import JWTError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.jwt_utils import JwtTokenUtil


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Lightweight JWT middleware.

    作用：
    - 读取 Authorization: Bearer <token>
    - 校验 JWT 与 Redis blacklist
    - 将 user_id 写入 request.state，供后续路由使用
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        request.state.user_id = None

        path = request.url.path
        # 当前公开接口白名单
        public_prefixes = (
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/sendForgetPasswordCode",
            "/api/v1/auth/forgetPassword",
        )
        swagger_public = ("/swagger", "/swagger-ui", "/v3/api-docs", "/webjars", "/docs", "/openapi.json", "/redoc")
        allow_health = path == "/health"

        is_public = path in public_prefixes or path.startswith(swagger_public) or allow_health
        if is_public:
            # 对公开接口也做一次 best-effort 解析，便于前端复用当前登录态
            await self._try_set_user_id(request)
            return await call_next(request)

        # 受保护路由：必须携带 Bearer token 且未被黑名单。
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(status_code=401, content={"message": "Unauthorized"})

        token = auth_header.removeprefix("Bearer ").strip()
        if not token:
            return JSONResponse(status_code=401, content={"message": "Unauthorized"})

        try:
            jwt_util = JwtTokenUtil()
            if not jwt_util.validate_token(token):
                return JSONResponse(status_code=401, content={"message": "Unauthorized"})

            claims = jwt_util.get_claims(token)
            if claims is None:
                return JSONResponse(status_code=401, content={"message": "Unauthorized"})

            request.state.user_id = claims.user_id
            return await call_next(request)
        except JWTError:
            return JSONResponse(status_code=401, content={"message": "Unauthorized"})
        except Exception:
            return JSONResponse(status_code=401, content={"message": "Unauthorized"})

    async def _try_set_user_id(self, request: Request) -> None:
        """
        Best-effort user_id extraction (non-blocking) for public endpoints.
        """
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return

        token = auth_header.removeprefix("Bearer ").strip()
        if not token:
            return

        try:
            jwt_util = JwtTokenUtil()
            claims = jwt_util.get_claims(token)
            if claims is not None and jwt_util.validate_token(token):
                request.state.user_id = claims.user_id
        except Exception:
            # Ignore for scaffold
            return
