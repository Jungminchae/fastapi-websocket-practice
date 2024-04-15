from fastapi import APIRouter
from app.routes import websockets
from app.routes import apis

router = APIRouter()

router.include_router(websockets.router, prefix="/ws")
router.include_router(apis.router, prefix="/apis")
