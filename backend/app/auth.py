"""Custom JWT auth: signup, login, profile, and the get_current_user dependency."""
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext

from . import config
from .db import users_table
from .models import (
    LoginRequest,
    Profile,
    ProfileUpdate,
    SignupRequest,
    TokenResponse,
)

router = APIRouter()

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
_bearer = HTTPBearer(auto_error=True)


def _hash_password(password: str) -> str:
    return _pwd.hash(password)


def _verify_password(password: str, password_hash: str) -> bool:
    return _pwd.verify(password, password_hash)


def _issue_token(user_id: str, email: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "email": email,
        "iat": now,
        "exp": now + timedelta(minutes=config.JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, config.get_jwt_secret(), algorithm=config.JWT_ALGORITHM)


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
) -> dict:
    """Validate the Bearer JWT and return the caller's user record."""
    try:
        payload = jwt.decode(
            creds.credentials,
            config.get_jwt_secret(),
            algorithms=[config.JWT_ALGORITHM],
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    email = payload.get("email")
    item = users_table().get_item(Key={"email": email}).get("Item")
    if not item:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists"
        )
    return item


@router.post("/auth/signup", response_model=TokenResponse, status_code=201)
def signup(req: SignupRequest):
    table = users_table()
    email = req.email.lower()
    user_id = str(uuid.uuid4())
    item = {
        "email": email,
        "user_id": user_id,
        "password_hash": _hash_password(req.password),
        "name": req.name,
        "contact": req.contact,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        # attribute_not_exists(email) => reject duplicate signups atomically
        table.put_item(Item=item, ConditionExpression="attribute_not_exists(email)")
    except table.meta.client.exceptions.ConditionalCheckFailedException:
        raise HTTPException(status_code=409, detail="Email already registered")

    return TokenResponse(access_token=_issue_token(user_id, email))


@router.post("/auth/login", response_model=TokenResponse)
def login(req: LoginRequest):
    email = req.email.lower()
    item = users_table().get_item(Key={"email": email}).get("Item")
    if not item or not _verify_password(req.password, item["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return TokenResponse(access_token=_issue_token(item["user_id"], email))


@router.get("/me", response_model=Profile)
def get_me(user: dict = Depends(get_current_user)):
    return Profile(**user)


@router.put("/me", response_model=Profile)
def update_me(req: ProfileUpdate, user: dict = Depends(get_current_user)):
    updates = {k: v for k, v in req.model_dump(exclude_unset=True).items()}
    if not updates:
        return Profile(**user)

    expr_names = {f"#{k}": k for k in updates}
    expr_values = {f":{k}": v for k, v in updates.items()}
    set_clause = ", ".join(f"#{k} = :{k}" for k in updates)
    resp = users_table().update_item(
        Key={"email": user["email"]},
        UpdateExpression=f"SET {set_clause}",
        ExpressionAttributeNames=expr_names,
        ExpressionAttributeValues=expr_values,
        ReturnValues="ALL_NEW",
    )
    return Profile(**resp["Attributes"])
