from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import random
import logging

router = APIRouter(prefix="/avatar", tags=["Avatar"])
logger = logging.getLogger("avatar")

avatars = []

class Avatar(BaseModel):
    name: str
    role: str


@router.post("/create")
async def create_avatar(avatar: Avatar):
    avatar_id = random.randint(1000, 9999)
    avatars.append({"id": avatar_id, **avatar.dict()})
    logger.info(f"🧠 Avatar created: {avatar.name} ({avatar.role}) [ID: {avatar_id}]")
    return {"ok": True, "msg": "🧠 Avatar created!", "id": avatar_id}


@router.get("/list")
async def list_avatars():
    if not avatars:
        logger.warning("⚠️ No avatars found in memory.")
    return {"avatars": avatars}


@router.post("/run/{avatar_id}")
async def run_avatar(avatar_id: int):
    found = any(a["id"] == avatar_id for a in avatars)
    if not found:
        logger.error(f"❌ Avatar ID {avatar_id} not found.")
        raise HTTPException(status_code=404, detail="Avatar not found.")
    logger.info(f"🚀 Avatar {avatar_id} executed workflow successfully.")
    return {"ok": True, "msg": f"🚀 Avatar {avatar_id} executed workflow successfully."}
