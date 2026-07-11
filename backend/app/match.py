"""/match — rank the user's bullets against a job description via Bedrock."""
import json

from boto3.dynamodb.conditions import Key
from fastapi import APIRouter, Depends, HTTPException

from .auth import get_current_user
from .bedrock import invoke_json
from .db import bullets_table
from .models import MatchRequest, MatchResponse

router = APIRouter()

_SYSTEM = (
    "You are a resume-tailoring assistant. Given a job description and a candidate's "
    "bullet bank, rank the most relevant bullets, identify keywords/skills the job "
    "wants that the bullets do not cover, and suggest an ordering. "
    "Respond with STRICT JSON only — no preamble, no markdown fences. "
    'Schema: {"ranked_bullets":[{"bullet_id":str,"reason":str}],'
    '"missing_keywords":[str],"suggested_order":[str]}. '
    "Only use bullet_id values that appear in the provided bank."
)


def _load_bullets(user_id: str):
    resp = bullets_table().query(KeyConditionExpression=Key("user_id").eq(user_id))
    return resp.get("Items", [])


def _bullet_for_prompt(item: dict) -> dict:
    return {
        "bullet_id": item["bullet_id"],
        "bullet": item.get("bullet"),
        "project": item.get("project"),
        "skills": item.get("skills", []),
        "category": item.get("category"),
        "impact_metric": item.get("impact_metric"),
    }


@router.post("/match", response_model=MatchResponse)
def match(req: MatchRequest, user: dict = Depends(get_current_user)):
    bullets = _load_bullets(user["user_id"])
    if not bullets:
        raise HTTPException(
            status_code=400,
            detail="No bullets stored yet. Add bullets or import a resume first.",
        )

    user_prompt = (
        "JOB DESCRIPTION:\n"
        f"{req.job_description}\n\n"
        "BULLET BANK (JSON):\n"
        f"{json.dumps([_bullet_for_prompt(b) for b in bullets])}"
    )
    result = invoke_json(_SYSTEM, user_prompt)
    return MatchResponse(**result)
