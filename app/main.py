import json
import os
import sys
import traceback
from typing import Optional
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pathlib import Path
import logging
from pydantic import BaseModel
from fastapi import UploadFile

app = FastAPI()


def configure_logging():
    LOGGING_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE_PATH = './log/backend.log'  # Specify the log file path

    logging.basicConfig(level=logging.INFO, format=LOGGING_FORMAT, filename=LOG_FILE_PATH)
    logging.getLogger("uvicorn").handlers = logging.getLogger().handlers


# Call the function to configure the logging
configure_logging()

# Create a logger
logger = logging.getLogger(__name__)


@app.get("/aiotts/update/info", tags=["AIO TTS"])
async def check_for_update():
    with open('./update/aiotts/update_info.json', 'r', encoding='utf-8') as f:
        update_info = json.load(f)

    return update_info


@app.get("/aiotts/update/download/data", tags=["AIO TTS"])
async def download_update_zip(version: str):
    file_path = Path(f"./update/aiotts/data/v{version}/main.zip")

    # Print the file path as the logger and return the file
    logger.info(f"Requested file path: {file_path}, Version: {version}")

    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        raise HTTPException(status_code=404, detail=f"File v{version}/main.zip not found")

    return FileResponse(file_path)


@app.get("/aiotts/update/download/metadata", tags=["AIO TTS"])
async def download_update_metadata(version: str):
    file_path = Path(f"./update/aiotts/data/v{version}/metadata.json")

    # Print the file path as the logger and return the file
    logger.info(f"Requested file path: {file_path}, Version: {version}")

    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        raise HTTPException(status_code=404, detail=f"File v{version}/metadata.json not found")

    return {
        'status': 'success',
        'message': 'File loaded successfully',
        'data': json.load(file_path.open('r', encoding='utf-8'))
    }


@app.post("/aiotts/update/upload", tags=["AIO TTS"])
async def upload_update(version: str, metadata_file: UploadFile = File(...), package_file: UploadFile = File(...)):
    file_extension = package_file.filename.split('.')[-1]
    if file_extension != "zip":
        raise HTTPException(status_code=400, detail="Only zip files are allowed for package")

    file_extension = metadata_file.filename.split('.')[-1]
    if file_extension != "json":
        raise HTTPException(status_code=400, detail="Only json files are allowed for metadata")

    os.makedirs(f"./update/aiotts/data/v{version}", exist_ok=True)

    # Save the file to the specified path
    try:
        file_path = Path(f"./update/aiotts/data/v{version}/main.zip")
        with file_path.open("wb") as buffer:
            buffer.write(await package_file.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error while saving the file: {str(e)}")

    # Update the metadata
    try:
        metadata_file_path = Path(f"./update/aiotts/data/v{version}/metadata.json")
        metadata = json.loads(metadata_file.file.read())
        with metadata_file_path.open("w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=4)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error while updating the metadata: {str(e)}")

    return {
        'status': 'success',
        'message': 'File uploaded successfully',
        'filename': package_file.filename,
        'version': version
    }


@app.post("/uploadfile/", tags=["AIO TTS"])
async def create_upload_file(file: UploadFile = File(...)):
    save_path = os.path.join(os.getcwd(), 'uploads', file.filename)

    if not os.path.exists(os.path.dirname(save_path)):
        os.makedirs(os.path.dirname(save_path))

    total_size = file.file.seek(0, 2)
    file.file.seek(0)

    with open(save_path, "wb") as buffer:
        logger.info(f"Saving file to: {save_path}")
        bytes_written = 0
        while True:
            chunk = await file.read(8192)
            if not chunk:
                break
            buffer.write(chunk)
            bytes_written += len(chunk)
            progress = (bytes_written / total_size) * 100
            print(f"Progress: {progress:.2f}%", end='\r')
        print()

    return {"filename": file.filename}

@app.get('/aiotts/installer', tags=["AIO TTS"])
def download_installer():
    file_path = Path(f"./uploads/AIO TikTokShop V2.rar")
    
    # Print the file path as the logger and return the file
    logger.info(f"Requested file path: {file_path}")
    
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        raise HTTPException(status_code=404, detail=f"File AIO TikTokShop V2.rar not found")
    
    return FileResponse(file_path, media_type='application/octet-stream', filename='AIO TikTokShop V2.rar')


@app.get("/aiotts/dependencies/ocr", tags=["AIO TTS"])
def download_ocr_dependencies():
    file_path = Path(f"./dependencies/Tesseract-OCR-Setup.exe")

    # Print the file path as the logger and return the file
    logger.info(f"Requested file path: {file_path}")

    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        raise HTTPException(status_code=404, detail=f"File Tesseract-OCR-Setup.exe not found")

    return FileResponse(file_path, media_type='application/octet-stream', filename='Tesseract-OCR-Setup.exe')

# Define Pydantic model for update_info
class UpdateInfo(BaseModel):
    latest: str
    date: str
    detail: str

@app.post("/aiotts/update/modify", tags=["AIO TTS"])
def modify_update_info_base(update_info: UpdateInfo):
    file_path = Path("./update/aiotts/update_info.json")
    
    with open(file_path, "w", encoding='utf-8') as f:
        json.dump(update_info.dict(), f, ensure_ascii=False, indent=4)
    
    return {"message": "Update info modified successfully"}

"""Auto PTS"""

@app.get("/autopts/update/info", tags=["Auto PTS"])
async def check_for_update():
    with open('./update/autopts/update_info.json', 'r', encoding='utf-8') as f:
        update_info = json.load(f)

    return update_info


@app.get("/autopts/update/download/data", tags=["Auto PTS"])
async def download_update_zip(version: str):
    file_path = Path(f"./update/autopts/data/v{version}/main.zip")

    # Print the file path as the logger and return the file
    logger.info(f"Requested file path: {file_path}, Version: {version}")

    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        raise HTTPException(status_code=404, detail=f"File v{version}/main.zip not found")

    return FileResponse(file_path)


@app.get("/autopts/update/download/metadata", tags=["Auto PTS"])
async def download_update_metadata(version: str):
    file_path = Path(f"./update/autopts/data/v{version}/metadata.json")

    # Print the file path as the logger and return the file
    logger.info(f"Requested file path: {file_path}, Version: {version}")

    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        raise HTTPException(status_code=404, detail=f"File v{version}/metadata.json not found")

    return {
        'status': 'success',
        'message': 'File loaded successfully',
        'data': json.load(file_path.open('r', encoding='utf-8'))
    }


@app.post("/autopts/update/upload", tags=["Auto PTS"])
async def upload_update(version: str, metadata_file: UploadFile = File(...), package_file: UploadFile = File(...)):
    file_extension = package_file.filename.split('.')[-1]
    if file_extension != "zip":
        raise HTTPException(status_code=400, detail="Only zip files are allowed for package")

    file_extension = metadata_file.filename.split('.')[-1]
    if file_extension != "json":
        raise HTTPException(status_code=400, detail="Only json files are allowed for metadata")

    os.makedirs(f"./update/autopts/data/v{version}", exist_ok=True)

    # Save the file to the specified path
    try:
        file_path = Path(f"./update/autopts/data/v{version}/main.zip")
        with file_path.open("wb") as buffer:
            buffer.write(await package_file.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error while saving the file: {str(e)}")

    # Update the metadata
    try:
        metadata_file_path = Path(f"./update/autopts/data/v{version}/metadata.json")
        metadata = json.loads(metadata_file.file.read())
        with metadata_file_path.open("w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=4)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error while updating the metadata: {str(e)}")

    return {
        'status': 'success',
        'message': 'File uploaded successfully',
        'filename': package_file.filename,
        'version': version
    }

@app.post("/autopts/update/modify", tags=["Auto PTS"])
def modify_update_info_base(update_info: UpdateInfo):
    file_path = Path("./update/autopts/update_info.json")
    
    with open(file_path, "w", encoding='utf-8') as f:
        json.dump(update_info.dict(), f, ensure_ascii=False, indent=4)
    
    return {"message": "Update info modified successfully"}

