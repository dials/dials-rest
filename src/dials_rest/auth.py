from __future__ import annotations

import logging
from datetime import datetime, timedelta

import jose.exceptions
import jose.jwt
from dateutil.tz import UTC
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .settings import Settings

logger = logging.getLogger(__name__)


SECRET_KEY = Settings().jwt_secret
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(
    data: dict, expires_delta: timedelta | None = None, expires: datetime = None
):
    to_encode = data.copy()
    if expires_delta and not expires:
        expires = datetime.utcnow() + expires_delta
    elif not expires:
        expires = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expires})
    encoded_jwt = jose.jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


class UserToken(HTTPAuthorizationCredentials):
    expiry: datetime

    @classmethod
    def from_jwt(cls, jwt: dict) -> UserToken:
        return cls(
            expiry=datetime.fromtimestamp(jwt["exp"], tz=UTC),
            scheme="bearer",
            credentials="",
        )


class JWTBearer(HTTPBearer):
    # https://github.com/tiangolo/fastapi/discussions/9085#discussioncomment-5543403
    __globals__ = globals()

    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> UserToken:
        token: HTTPAuthorizationCredentials = await super().__call__(request)
        if token:
            if not token.scheme == "Bearer":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication scheme",
                )
            try:
                data = jose.jwt.decode(
                    token.credentials, SECRET_KEY, algorithms=[ALGORITHM]
                )
            except jose.exceptions.ExpiredSignatureError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Expired token",
                )
            except jose.exceptions.JWTError:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication token",
                )
            return UserToken.from_jwt(data)
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization credentials.",
            )
