"""Pydantic request/response models."""
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


# --- Auth / profile ---
class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: Optional[str] = None
    contact: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    contact: Optional[str] = None
    headline: Optional[str] = None


class Profile(BaseModel):
    email: EmailStr
    user_id: str
    name: Optional[str] = None
    contact: Optional[str] = None
    headline: Optional[str] = None
    created_at: Optional[str] = None


# --- Bullets ---
class BulletInput(BaseModel):
    bullet: str
    project: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    category: Optional[str] = None
    impact_metric: Optional[str] = None


class Bullet(BulletInput):
    bullet_id: str
    source: str = "manual"


# --- Resume import ---
class ResumeImportRequest(BaseModel):
    filename: str
    # base64-encoded file contents (PDF or DOCX)
    content_base64: str


class ResumeImportResponse(BaseModel):
    imported: int
    bullets: List[Bullet]


# --- Match ---
class MatchRequest(BaseModel):
    job_description: str = Field(min_length=1)


class RankedBullet(BaseModel):
    bullet_id: str
    reason: str


class MatchResponse(BaseModel):
    ranked_bullets: List[RankedBullet]
    missing_keywords: List[str]
    suggested_order: List[str]


# --- Generate CV ---
class GenerateCVRequest(BaseModel):
    job_description: str = Field(min_length=1)


class GenerateCVResponse(BaseModel):
    tex: str
    filename: str
    # The structured content the LaTeX was rendered from (handy for previews).
    content: dict
