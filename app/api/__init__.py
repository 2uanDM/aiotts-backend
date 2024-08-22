from fastapi import APIRouter

from .routes import auth, download_tools, google_sheet, updater

api_router = APIRouter()
api_router.include_router(
    updater.router, prefix="/aiotts/update", tags=["Update AIOTTS"]
)
api_router.include_router(
    download_tools.router,
    prefix="/aiotts",
    tags=["Download executable file and Dependencies"],
)
api_router.include_router(auth.router, prefix="/aiotts/auth", tags=["Authentication"])
api_router.include_router(google_sheet.router, prefix="/aiotts/order", tags=["Orders"])


__all__ = ["api_router"]
