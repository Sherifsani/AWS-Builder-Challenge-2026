"""Bullet-bank CRUD, always scoped to the caller's user_id."""
import uuid
from typing import List

from boto3.dynamodb.conditions import Key
from fastapi import APIRouter, Depends, HTTPException

from .auth import get_current_user
from .db import bullets_table
from .models import Bullet, BulletInput

router = APIRouter()


def _new_bullet_id() -> str:
    return "b" + uuid.uuid4().hex[:8]


def store_bullets(user_id: str, inputs: List[BulletInput], source: str) -> List[Bullet]:
    """Persist a batch of bullets for a user; returns the created Bullet models."""
    table = bullets_table()
    created: List[Bullet] = []
    with table.batch_writer() as batch:
        for inp in inputs:
            bullet = Bullet(bullet_id=_new_bullet_id(), source=source, **inp.model_dump())
            batch.put_item(Item={"user_id": user_id, **bullet.model_dump()})
            created.append(bullet)
    return created


@router.post("/bullets", response_model=Bullet, status_code=201)
def add_bullet(req: BulletInput, user: dict = Depends(get_current_user)):
    return store_bullets(user["user_id"], [req], source="manual")[0]


@router.get("/bullets", response_model=List[Bullet])
def list_bullets(user: dict = Depends(get_current_user)):
    resp = bullets_table().query(
        KeyConditionExpression=Key("user_id").eq(user["user_id"])
    )
    return [Bullet(**item) for item in resp.get("Items", [])]


@router.put("/bullets/{bullet_id}", response_model=Bullet)
def update_bullet(
    bullet_id: str, req: BulletInput, user: dict = Depends(get_current_user)
):
    table = bullets_table()
    existing = table.get_item(
        Key={"user_id": user["user_id"], "bullet_id": bullet_id}
    ).get("Item")
    if not existing:
        raise HTTPException(status_code=404, detail="Bullet not found")
    bullet = Bullet(
        bullet_id=bullet_id, source=existing.get("source", "manual"), **req.model_dump()
    )
    table.put_item(Item={"user_id": user["user_id"], **bullet.model_dump()})
    return bullet


@router.delete("/bullets/{bullet_id}", status_code=204)
def delete_bullet(bullet_id: str, user: dict = Depends(get_current_user)):
    bullets_table().delete_item(
        Key={"user_id": user["user_id"], "bullet_id": bullet_id}
    )
    return None
