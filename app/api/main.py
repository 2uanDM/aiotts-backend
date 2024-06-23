from fastapi import APIRouter

from app.api.routes import auth, label

api_router = APIRouter()
api_router.include_router(label.router, prefix="/aiotts/label", tags=["Orders"])
api_router.include_router(auth.router, prefix="/aiotts/auth", tags=["Authentication"])
