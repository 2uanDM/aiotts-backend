import json
import logging
import os
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.api.schema.updater import UpdateInfo
from app.utils import setup_logger

logger = logging.getLogger(__name__)
setup_logger(logger)

router = APIRouter()


@router.get("/info")
async def check_for_update():
    with open("./update/aiotts/update_info.json", "r", encoding="utf-8") as f:
        update_info = json.load(f)

    return update_info


@router.get("/download/data")
async def download_update_zip(version: str):
    file_path = Path(f"./update/aiotts/data/v{version}/main.zip")

    # Print the file path as the logger and return the file
    logger.info(f"Requested file path: {file_path}, Version: {version}")

    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        raise HTTPException(
            status_code=404, detail=f"File v{version}/main.zip not found"
        )

    return FileResponse(file_path)


@router.get("/download/metadata")
async def download_update_metadata(version: str):
    file_path = Path(f"./update/aiotts/data/v{version}/metadata.json")

    # Print the file path as the logger and return the file
    logger.info(f"Requested file path: {file_path}, Version: {version}")

    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        raise HTTPException(
            status_code=404, detail=f"File v{version}/metadata.json not found"
        )

    return {
        "status": "success",
        "message": "File loaded successfully",
        "data": json.load(file_path.open("r", encoding="utf-8")),
    }


@router.post("/upload", tags=["Update AIOTTS"])
async def upload_update(
    version: str,
    metadata_file: UploadFile = File(...),
    package_file: UploadFile = File(...),
):
    file_extension = package_file.filename.split(".")[-1]
    if file_extension != "zip":
        raise HTTPException(
            status_code=400, detail="Only zip files are allowed for package"
        )

    file_extension = metadata_file.filename.split(".")[-1]
    if file_extension != "json":
        raise HTTPException(
            status_code=400, detail="Only json files are allowed for metadata"
        )

    os.makedirs(f"./update/aiotts/data/v{version}", exist_ok=True)

    # Save the file to the specified path
    try:
        file_path = Path(f"./update/aiotts/data/v{version}/main.zip")
        with file_path.open("wb") as buffer:
            buffer.write(await package_file.read())
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error while saving the file: {str(e)}"
        )

    # Update the metadata
    try:
        metadata_file_path = Path(f"./update/aiotts/data/v{version}/metadata.json")
        metadata = json.loads(metadata_file.file.read())
        with metadata_file_path.open("w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=4)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error while updating the metadata: {str(e)}"
        )

    return {
        "status": "success",
        "message": "File uploaded successfully",
        "filename": package_file.filename,
        "version": version,
    }


@router.post("/modify")
def modify_update_info_base(update_info: UpdateInfo):
    file_path = Path("./update/aiotts/update_info.json")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(update_info.dict(), f, ensure_ascii=False, indent=4)

    return {"message": "Update info modified successfully"}
