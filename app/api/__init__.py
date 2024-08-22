from fastapi import APIRouter

from .routes import auth, google_sheet, label

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/aiotts/auth", tags=["Authentication"])
# api_router.include_router(label.router, prefix="/aiotts/label", tags=["Orders"])
api_router.include_router(google_sheet.router, prefix="/aiotts/order", tags=["Orders"])

__all__ = ["api_router"]
