from typing import Optional

import httpx
from fastapi import Header, HTTPException

from app.core.config import settings
from app.core.security import decode_access_token
from app.db.session import DEMO_USER_ID


def _supabase_project_ref() -> Optional[str]:
    url = settings.supabase_url.strip().rstrip("/")
    if not url.startswith("http"):
        return None
    return url.split("//", 1)[-1].split(".", 1)[0]


def get_current_claims(authorization: Optional[str] = Header(default=None)) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ", 1)[1].strip()
    claims = decode_access_token(token)
    if not claims:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return claims


async def get_current_user_id(authorization: Optional[str] = Header(default=None)) -> str:
    """Return the authenticated user id.

    Local email/password tokens are preferred. Supabase bearer tokens are still
    accepted if configured. With no token, a seeded demo user is used.
    """
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        claims = decode_access_token(token)
        if claims and claims.get("sub"):
            return str(claims["sub"])

        project_ref = _supabase_project_ref()
        if project_ref and settings.supabase_anon_key and token:
            try:
                async with httpx.AsyncClient(timeout=8.0) as client:
                    response = await client.get(
                        f"https://{project_ref}.supabase.co/auth/v1/user",
                        headers={
                            "Authorization": f"Bearer {token}",
                            "apikey": settings.supabase_anon_key,
                        },
                    )
                if response.status_code == 200:
                    user_id = response.json().get("id")
                    if user_id:
                        return str(user_id)
            except Exception:
                pass

    return DEMO_USER_ID
