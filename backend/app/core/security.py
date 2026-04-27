"""Password hashing, JWT issuance, and request-time authentication.

Three things live here:

  1. **Password hashing** with bcrypt. We never store raw passwords — only
     a one-way hash. ``verify_password`` checks a candidate against the
     stored hash without ever decrypting anything (it can't — that's the
     point of a one-way function).

  2. **JWT (JSON Web Token) creation.** A JWT is a signed, base64-encoded
     blob with three parts: header.payload.signature. The payload here
     contains the user id (``sub``), their role, and an expiry. Anyone can
     *read* a JWT (it's not encrypted), but only someone with ``JWT_SECRET``
     can produce a valid signature — so the server can trust it.

  3. **Dependencies** (``get_current_user``, ``require_manager``,
     ``require_member``). FastAPI injects these into routes. They:
       a) extract the JWT from the ``Authorization: Bearer ...`` header,
       b) decode and verify it,
       c) load the user from the DB,
       d) optionally check the user's role.

For an enterprise-grade replacement (Keycloak, Auth0), see CONTRIBUTING.md
→ "Authentication & Identity". The interface here would stay similar: routes
still depend on ``require_manager``/``require_member``, only the *how* changes.
"""

from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.models.user import User, UserRole

# passlib lets us swap algorithms later (e.g. argon2) without changing call sites.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ``tokenUrl`` tells Swagger UI where its "Authorize" button should POST
# username/password to obtain a token. We expose a form endpoint at
# /auth/login/form to satisfy this — the JSON endpoint at /auth/login is the
# one the frontend actually calls.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def hash_password(password: str) -> str:
    """One-way hash a password. Different output every time (random salt)."""
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Constant-time check of a candidate against the stored hash."""
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str, role: str) -> str:
    """Build a signed JWT carrying the user id and role.

    The ``exp`` claim is what makes the token expire — clients have to log in
    again afterward. Short-lived access tokens + a separate refresh token is
    the standard production pattern (left as a contribution opportunity).
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {"sub": subject, "role": role, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Decode the JWT, then fetch the matching user row.

    We re-load the user every request rather than trusting the token blindly.
    Why? If the user is deleted or their role changes, the next request will
    notice. The trade-off is one DB query per request — usually fine, and
    cacheable with Redis if it ever becomes a hot path.
    """
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_error
    except JWTError:
        # Catches expired tokens, bad signatures, malformed JWTs — anything
        # that means we should NOT trust the token.
        raise credentials_error

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_error
    return user


def require_manager(user: User = Depends(get_current_user)) -> User:
    """Route dependency: 403 if the caller isn't a manager."""
    if user.role != UserRole.MANAGER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager access required",
        )
    return user


def require_member(user: User = Depends(get_current_user)) -> User:
    """Route dependency: 403 if the caller isn't a member."""
    if user.role != UserRole.MEMBER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Member access required",
        )
    return user
