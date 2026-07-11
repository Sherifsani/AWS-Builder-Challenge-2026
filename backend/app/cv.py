"""/generate-cv — compose a tailored CV (LaTeX source) from the user's bullets.

Bedrock returns structured JSON *content only*; app.latex_template turns it into a
compile-safe .tex document. No LaTeX ever comes from the model, so it can't emit
broken macros.
"""
import json

from boto3.dynamodb.conditions import Key
from fastapi import APIRouter, Depends, HTTPException

from .auth import get_current_user
from .bedrock import invoke_json
from .db import bullets_table
from .latex_template import render_cv
from .models import GenerateCVRequest, GenerateCVResponse

router = APIRouter()

_SYSTEM = (
    "You are a resume writer. Given a job description, the candidate's profile, and "
    "their bullet bank, produce the CONTENT for a one-page tailored CV. "
    "Select and lightly rephrase the most relevant bullets to mirror the job's "
    "language, but do NOT invent experience — only use facts present in the bullets. "
    "Order experience and bullets by relevance to the job. "
    "Respond with STRICT JSON only — no preamble, no markdown fences, no LaTeX. "
    'Schema: {"name":str,"headline":str,"contact":str,"summary":str,'
    '"experience":[{"project":str,"bullets":[str]}],"skills":[str]}'
)


def _load_bullets(user_id: str):
    resp = bullets_table().query(KeyConditionExpression=Key("user_id").eq(user_id))
    return resp.get("Items", [])


def _bullet_for_prompt(item: dict) -> dict:
    return {
        "bullet": item.get("bullet"),
        "project": item.get("project"),
        "skills": item.get("skills", []),
        "category": item.get("category"),
        "impact_metric": item.get("impact_metric"),
    }


@router.post("/generate-cv", response_model=GenerateCVResponse)
def generate_cv(req: GenerateCVRequest, user: dict = Depends(get_current_user)):
    bullets = _load_bullets(user["user_id"])
    if not bullets:
        raise HTTPException(
            status_code=400,
            detail="No bullets stored yet. Add bullets or import a resume first.",
        )

    profile = {
        "name": user.get("name"),
        "contact": user.get("contact") or user.get("email"),
        "headline": user.get("headline"),
    }
    user_prompt = (
        "JOB DESCRIPTION:\n"
        f"{req.job_description}\n\n"
        "PROFILE (JSON):\n"
        f"{json.dumps(profile)}\n\n"
        "BULLET BANK (JSON):\n"
        f"{json.dumps([_bullet_for_prompt(b) for b in bullets])}"
    )

    content = invoke_json(_SYSTEM, user_prompt, max_tokens=3000)
    # Fall back to the stored profile if the model omitted header fields.
    content.setdefault("name", profile["name"])
    content.setdefault("contact", profile["contact"])
    content.setdefault("headline", profile["headline"])

    tex = render_cv(content)
    return GenerateCVResponse(tex=tex, filename="tailored-cv.tex", content=content)
