import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.utils import setup_logger

logger = logging.getLogger(__name__)
setup_logger(logger)

router = APIRouter()


@router.get("/installer")
def download_installer(file_name: str):
    file_path = Path(f"./uploads/{file_name}")

    # Print the file path as the logger and return the file
    logger.info(f"Requested file path: {file_path}")

    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        raise HTTPException(status_code=404, detail=f"File {file_name} not found")

    return FileResponse(
        file_path,
        media_type="application/octet-stream",
        filename=file_name,
    )


@router.get("/dependencies/ocr")
def download_ocr_dependencies():
    file_path = Path("./dependencies/Tesseract-OCR-Setup.exe")

    # Print the file path as the logger and return the file
    logger.info(f"Requested file path: {file_path}")

    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        raise HTTPException(
            status_code=404, detail="File Tesseract-OCR-Setup.exe not found"
        )

    return FileResponse(
        file_path,
        media_type="application/octet-stream",
        filename="Tesseract-OCR-Setup.exe",
    )
