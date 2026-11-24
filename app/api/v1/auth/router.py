from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_claims
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models import Profile
from app.schemas.auth import AuthResponse, LoginRequest, SignupRequest, UserResponse

router = APIRouter(tags=["auth"])


def _auth_response(profile: Profile) -> AuthResponse:
    token = create_access_token(profile.id, profile.email)
    return AuthResponse(
        access_token=token,
        user=UserResponse(id=profile.id, email=profile.email, full_name=profile.full_name),
    )


def _valid_email(email: str) -> bool:
    return "@" in email and "." in email.split("@", 1)[-1]


@router.post("/signup", response_model=AuthResponse, status_code=201)
async def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    if not _valid_email(email):
        raise HTTPException(status_code=400, detail="Invalid email address")

    existing = db.scalar(select(Profile).where(Profile.email == email))
    if existing:
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    profile = Profile(
        id=str(uuid4()),
        email=email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        is_active=True,
        is_verified=True,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return _auth_response(profile)


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    profile = db.scalar(select(Profile).where(Profile.email == email))
    if not profile or not verify_password(payload.password, profile.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return _auth_response(profile)


@router.get("/me", response_model=UserResponse)
async def me(
    claims: dict = Depends(get_current_claims),
    db: Session = Depends(get_db),
):
    profile = db.get(Profile, claims.get("sub"))
    if not profile:
        raise HTTPException(status_code=401, detail="Account not found")
    return UserResponse(id=profile.id, email=profile.email, full_name=profile.full_name)
