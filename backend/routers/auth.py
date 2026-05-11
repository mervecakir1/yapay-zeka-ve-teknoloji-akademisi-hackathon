"""
JWT auth flow:
  POST /users   register  → kullanıcı oluşur, token verilmez (login'e gidilir)
  POST /login   login     → {access_token, token_type, user}

Korumalı endpoint'ler `Depends(get_current_user)` ile auth zorunlu kılar.
Frontend her isteğe `Authorization: Bearer <token>` header'ı ekler.
"""
from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from starlette import status

from ..database import db_dependency
from ..models import User
from ..schemas import UserCreate, LoginRequest

# Demo için sabit; production'da .env'den okunmalı
SECRET_KEY = "acoztm3revp1vfj7ld5sz2ndg5xp79r9fnr2p4hx2dy63h6a8efhj6rm54u8evh8"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

router = APIRouter(tags=["Auth"])

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl="/login", auto_error=False)


def _serialize_user(user: User) -> dict:
    return {
        "user_id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
    }


def create_access_token(user_id: int, email: str, role: str, expires_delta: timedelta) -> str:
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    token: Annotated[Optional[str], Depends(oauth2_bearer)],
    db: db_dependency,
) -> dict:
    """Korumalı endpoint'lerin bağımlılığı. Token yoksa veya geçersizse 401."""
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exc
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exc
        user_id = int(user_id_str)
    except (JWTError, ValueError):
        raise credentials_exc

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exc
    return _serialize_user(user)


user_dependency = Annotated[dict, Depends(get_current_user)]


# ===== Role-based access control =====

# Backend tarafında kabul edilen rol isimleri (frontend dropdown'ıyla aynı)
ROLE_ADMIN = "Admin"
ROLE_BUSINESS_OWNER = "Business Owner"
ROLE_SALES_MANAGER = "Sales Manager"
ROLE_INVENTORY_STAFF = "Inventory Staff"

ADMIN_ROLES = {ROLE_ADMIN, ROLE_BUSINESS_OWNER}
SALES_ROLES = ADMIN_ROLES | {ROLE_SALES_MANAGER}
INVENTORY_ROLES = ADMIN_ROLES | {ROLE_INVENTORY_STAFF}


def require_roles(*allowed: str):
    """
    Dependency factory. Yetkili rolleri parametre olarak alır,
    izinsiz kullanıcıya 403 atar.

    Kullanım:
        @router.post("/products")
        def create(payload, user: dict = Depends(require_roles("Admin", "Business Owner"))): ...
    """
    allowed_set = set(allowed)

    def dependency(user: dict = Depends(get_current_user)) -> dict:
        if user.get("role") not in allowed_set:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required role: {', '.join(sorted(allowed_set))}. Your role: {user.get('role')}",
            )
        return user

    return dependency


@router.get("/users")
def get_users(
    db: db_dependency,
    user: dict = Depends(require_roles(ROLE_ADMIN, ROLE_BUSINESS_OWNER)),
):
    return [_serialize_user(u) for u in db.query(User).all()]


@router.post("/users", status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: db_dependency):
    # Email zaten kayıtlı mı?
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists.")

    # Email format basit kontrol (Pydantic EmailStr eklenmediği için minimal)
    if "@" not in payload.email or "." not in payload.email.split("@")[-1]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email format.")

    if len(payload.password) < 4:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Password must be at least 4 characters.")

    user = User(
        name=payload.name.strip(),
        email=payload.email.strip().lower(),
        hashed_password=bcrypt_context.hash(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "User created successfully. Please login.", "user": _serialize_user(user)}


@router.post("/login")
def login(payload: LoginRequest, db: db_dependency):
    email_normalized = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email_normalized).first()
    if user is None or not bcrypt_context.verify(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

    token = create_access_token(
        user_id=user.id,
        email=user.email,
        role=user.role,
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return {
        "message": "Login successful",
        "access_token": token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": _serialize_user(user),
    }


@router.get("/me")
def get_me(user: user_dependency):
    """Mevcut kullanıcı bilgisi — frontend token doğrulaması için kullanabilir."""
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    db: db_dependency,
    user_id: int,
    user: dict = Depends(require_roles(ROLE_ADMIN)),
):
    target = db.query(User).filter(User.id == user_id).first()
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    db.delete(target)
    db.commit()
