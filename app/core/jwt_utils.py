from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from typing import Any, Optional

import redis
from jose import JWTError, jwt

from app.core.settings import get_settings


@dataclass(frozen=True)
class JwtClaims:
    user_id: int
    username: str


_redis_client: redis.Redis | None = None


def get_redis_client() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _blacklist_key(token: str) -> str:
    return f"jwt:blacklist:{_token_hash(token)}"


class JwtTokenUtil:
    def __init__(self) -> None:
        self.settings = get_settings()

    def generate_access_token(self, user_id: int, username: str) -> str:
        now = int(time.time())
        exp = now + int(self.settings.jwt_access_token_expiration)
        payload: dict[str, Any] = {
            "userId": user_id,
            "username": username,
            "sub": username,
            "iat": now,
            "exp": exp,
        }
        return jwt.encode(payload, self.settings.jwt_secret, algorithm="HS512")

    def _remaining_seconds(self, token: str) -> int:
        # blacklist TTL 至少覆盖 token 的剩余有效期，避免退出后立刻重新生效。
        try:
            payload = jwt.decode(
                token,
                self.settings.jwt_secret,
                algorithms=["HS512"],
                options={"verify_exp": False},
            )
            exp = payload.get("exp")
            if exp is None:
                return int(self.settings.jwt_access_token_expiration)
            remaining = int(exp) - int(time.time())
            ttl = max(int(self.settings.jwt_access_token_expiration), remaining)
            return max(ttl, 1)
        except Exception:
            return int(self.settings.jwt_access_token_expiration)

    def add_token_to_blacklist(self, token: str) -> None:
        if not token:
            return
        client = get_redis_client()
        key = _blacklist_key(token)
        ttl_seconds = self._remaining_seconds(token)
        client.set(key, "invalid", ex=ttl_seconds)

    def is_token_blacklisted(self, token: str) -> bool:
        if not token:
            return False
        client = get_redis_client()
        key = _blacklist_key(token)
        return bool(client.exists(key))

    def get_claims(self, token: str) -> Optional[JwtClaims]:
        if not token:
            return None
        try:
            payload = jwt.decode(token, self.settings.jwt_secret, algorithms=["HS512"])
            user_id = payload.get("userId")
            username = payload.get("username") or payload.get("sub")
            if user_id is None or username is None:
                return None
            return JwtClaims(user_id=int(user_id), username=str(username))
        except JWTError:
            return None
        except Exception:
            return None

    def validate_token(self, token: str) -> bool:
        if not token:
            return False
        if self.is_token_blacklisted(token):
            return False
        return self.get_claims(token) is not None
