import json
import uuid
from typing import Annotated
from redis import asyncio as aioredis
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from app.service.redis import get_redis_pool


router = APIRouter()

@router.post("/session/")
async def create_session(redis: Annotated[aioredis.Redis, Depends(get_redis_pool)]):
    """
    Session 생성
    - 방장이 방을 생성한다.
    """
    session_id = str(uuid.uuid4())
    
    session_data = {
        "participants": [],
        "menu": [],
        "expires_at": (datetime.now() + timedelta(minutes=10)).isoformat()
    }

    await redis.set(session_id, json.dumps(session_data), ex=600)
    return {"url": f"/ws/{session_id}/"}


@router.post("/extend-session/{session_id}/")
async def extend_session(session_id: str, redis: Annotated[aioredis.Redis, Depends(get_redis_pool)]):
    """
    10분이 지나도 메뉴를 못골랐다면 연장해라
    - 방폭을 10분 연장한다.
    """
    session_data = await redis.get(session_id)
    if not session_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="세션 없음")

    session_data = json.loads(session_data)

    expires_at = datetime.fromisoformat(session_data["expires_at"])
    expires_at += timedelta(minutes=10)
    session_data["expires_at"] = expires_at.isoformat()

    await redis.set(session_id, json.dumps(session_data), ex=(expires_at - datetime.now()).seconds)
    return {"success": True}
