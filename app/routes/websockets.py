import asyncio
import json
from redis import asyncio as aioredis
from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, WebSocket, Depends, HTTPException, status
from fastapi.websockets import WebSocketDisconnect
from app.service.redis import get_redis_pool
from app.service.managers import ws_manager, MaximumSessionReachException, MaximumConnectionPerSessionReachException
from app.service.sessions import update_session_expiration, add_participant_to_session

router = APIRouter()

@router.websocket("/{session_id}/")
async def menu_websocket_endpoint(
    websocket: WebSocket, 
    session_id: str,
    redis: Annotated[aioredis.Redis, Depends(get_redis_pool)]
    ):
    try:
        session_data = await redis.get(session_id)
        if not session_data:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="세션 없음")
        session_data = json.loads(session_data)

        if len(session_data["participants"]) >= 10:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="최대 참가자 수 초과")

        pubsub = redis.pubsub()
        await pubsub.subscribe(session_id)

        await websocket.accept()
        try:
            ws_manager.add_client(session_id, websocket)
        except MaximumSessionReachException:            
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="최대 세션 수 초과")
        except MaximumConnectionPerSessionReachException:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="최대 연결 수 초과")
        
        await add_participant_to_session(session_data, websocket.client)
        await update_session_expiration(session_data)
        await redis.set(session_id, json.dumps(session_data), ex=(datetime.fromisoformat(session_data["expires_at"]) - datetime.now()).seconds)
        try:
            ws_manager.add_client(session_id, websocket)
            while True:
                received_data = await websocket.receive_text()
                command, menu_item = received_data.split(":", 1)

                if command.lower() == "add":
                    session_data["menu"].append(menu_item)
                elif command.lower() == "remove":
                    session_data["menu"].remove(menu_item)
                expire_seconds = (datetime.fromisoformat(session_data["expires_at"]) - datetime.now()).total_seconds()
                await redis.set(session_id, json.dumps(session_data), ex=int(expire_seconds))
            
                await redis.publish(session_id, json.dumps(session_data["menu"]))
                await asyncio.sleep(0.1)
                while True:
                    message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=5)
                    if message:
                        updated_menu = json.loads(message['data'])
                        clients = ws_manager.get_clients(session_id)
                        for client in clients:
                            await client.send_json(updated_menu)
                    else:
                        if message is None:
                            try:
                                session_data = await redis.get(session_id)
                                session_data = json.loads(session_data)
                                clients = ws_manager.get_clients(session_id)
                                for client in clients:
                                    await client.send_json(session_data["menu"])
                            except Exception:
                                pass
                        break  
                    await asyncio.sleep(0.1) 

        except WebSocketDisconnect:
            ws_manager.remove_client(session_id, websocket)
            await redis.delete(session_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) 