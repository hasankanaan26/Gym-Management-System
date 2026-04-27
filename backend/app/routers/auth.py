"""Authentication endpoints.

Endpoints exposed:
  POST /auth/register     — public; creates a member account, returns a JWT
  POST /auth/login        — public; email+password JSON, returns a JWT
  POST /auth/login/form   — same, but accepts form-encoded data so Swagger's
                            "Authorize" button works (hidden from /docs UI)
  GET  /auth/me           — returns the currently logged-in user

The frontend uses the JSON ``/auth/login`` route. The form variant exists
purely so you can click "Authorize" in Swagger and try secured endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.models.user import User, UserRole
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserOut

# A router groups related endpoints. The ``prefix`` is prepended to every
# path inside, and ``tags`` controls how Swagger groups them in the UI.
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    """Create a new member account.

    Public endpoint — used by the frontend's signup page. Manager accounts
    aren't created this way; they're created via the seed script or directly
    in the DB. (You could add a "first user is a manager" rule, or an
    invitation flow — both are good contribution ideas.)
    """
    # Check for duplicates *before* hashing — bcrypt is slow on purpose, no
    # need to burn CPU just to fail.
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    user = User(
        email=body.email,
        name=body.name,
        password_hash=hash_password(body.password),
        role=UserRole.MEMBER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # We return a token immediately so the frontend doesn't have to make a
    # second login call after a successful signup.
    token = create_access_token(subject=str(user.id), role=user.role.value)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login_json(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    # IMPORTANT: return the *same* error for "wrong email" and "wrong password".
    # Otherwise the API leaks which emails are registered (account enumeration).
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token = create_access_token(subject=str(user.id), role=user.role.value)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/login/form", response_model=TokenResponse, include_in_schema=False)
def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """OAuth2 password-flow endpoint for Swagger's Authorize button.

    Hidden from the docs (``include_in_schema=False``) because it duplicates
    /login — its only job is to satisfy the OAuth2PasswordBearer scheme.
    """
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token = create_access_token(subject=str(user.id), role=user.role.value)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    """Returns the currently logged-in user.

    Useful for the frontend on page load to see "is the saved token still
    valid? if so, who am I?".
    """
    return current_user
