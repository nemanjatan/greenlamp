"""Single-password gate for the demo deployment.

We don't need real user accounts — just a way to keep casual visitors from
spending the OpenAI / AssemblyAI / Uploadcare budget. The frontend shows a
password page, posts to /api/auth/login, the backend sets an HttpOnly cookie,
and protected routes (/api/jobs*) require that cookie via FastAPI's Depends.
"""

from __future__ import annotations

import os

from fastapi import Cookie, HTTPException, Response

COOKIE_NAME = "wtf_session"
COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24 * 30  # 30 days


def _get_demo_password() -> str:
    pwd = os.environ.get("DEMO_PASSWORD")
    if not pwd:
        raise RuntimeError(
            "DEMO_PASSWORD env var is not set. The web demo requires a shared "
            "password to gate access to the pipeline."
        )
    return pwd


def login(password: str, response: Response) -> dict:
    if password != _get_demo_password():
        raise HTTPException(status_code=401, detail="Invalid password")
    response.set_cookie(
        key=COOKIE_NAME,
        value=password,
        httponly=True,
        secure=True,
        samesite="strict",
        max_age=COOKIE_MAX_AGE_SECONDS,
        path="/",
    )
    return {"ok": True}


def logout(response: Response) -> dict:
    response.delete_cookie(key=COOKIE_NAME, path="/")
    return {"ok": True}


def require_auth(session: str | None = Cookie(default=None, alias=COOKIE_NAME)) -> None:
    if not session or session != _get_demo_password():
        raise HTTPException(status_code=401, detail="Authentication required")


def check_auth(session: str | None = Cookie(default=None, alias=COOKIE_NAME)) -> dict:
    return {"authenticated": bool(session) and session == _get_demo_password()}
