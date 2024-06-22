import json
import logging
import os
from pathlib import Path

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from app.utils.database import server_connection

load_dotenv(override=True)

app = FastAPI()
API_KEY = os.getenv("API_KEY")


def configure_logging():
    LOGGING_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE_PATH = "./log/backend.log"  # Specify the log file path

    logging.basicConfig(
        level=logging.INFO, format=LOGGING_FORMAT, filename=LOG_FILE_PATH
    )
    logging.getLogger("uvicorn").handlers = logging.getLogger().handlers


# Call the function to configure the logging
configure_logging()

# Create a logger
logger = logging.getLogger(__name__)


@app.get("/aiotts/update/info", tags=["AIO TTS"])
async def check_for_update():
    with open("./update/aiotts/update_info.json", "r", encoding="utf-8") as f:
        update_info = json.load(f)

    return update_info


@app.get("/aiotts/update/download/data", tags=["AIO TTS"])
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


@app.get("/aiotts/update/download/metadata", tags=["AIO TTS"])
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


@app.post("/aiotts/update/upload", tags=["AIO TTS"])
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


@app.post("/uploadfile/", tags=["AIO TTS"])
async def create_upload_file(file: UploadFile = File(...)):
    save_path = os.path.join(os.getcwd(), "uploads", file.filename)

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
            print(f"Progress: {progress:.2f}%", end="\r")
        print()

    return {"filename": file.filename}


@app.get("/aiotts/installer", tags=["AIO TTS"])
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


@app.get("/aiotts/dependencies/ocr", tags=["AIO TTS"])
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


# Define Pydantic model for update_info
class UpdateInfo(BaseModel):
    latest: str
    date: str
    detail: str


@app.post("/aiotts/update/modify", tags=["AIO TTS"])
def modify_update_info_base(update_info: UpdateInfo):
    file_path = Path("./update/aiotts/update_info.json")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(update_info.dict(), f, ensure_ascii=False, indent=4)

    return {"message": "Update info modified successfully"}


"""Auto PTS"""


@app.get("/autopts/update/info", tags=["Auto PTS"])
async def check_for_update():
    with open("./update/autopts/update_info.json", "r", encoding="utf-8") as f:
        update_info = json.load(f)

    return update_info


@app.get("/autopts/update/download/data", tags=["Auto PTS"])
async def download_update_zip(version: str):
    file_path = Path(f"./update/autopts/data/v{version}/main.zip")

    # Print the file path as the logger and return the file
    logger.info(f"Requested file path: {file_path}, Version: {version}")

    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        raise HTTPException(
            status_code=404, detail=f"File v{version}/main.zip not found"
        )

    return FileResponse(file_path)


@app.get("/autopts/update/download/metadata", tags=["Auto PTS"])
async def download_update_metadata(version: str):
    file_path = Path(f"./update/autopts/data/v{version}/metadata.json")

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


@app.post("/autopts/update/upload", tags=["Auto PTS"])
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

    os.makedirs(f"./update/autopts/data/v{version}", exist_ok=True)

    # Save the file to the specified path
    try:
        file_path = Path(f"./update/autopts/data/v{version}/main.zip")
        with file_path.open("wb") as buffer:
            buffer.write(await package_file.read())
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error while saving the file: {str(e)}"
        )

    # Update the metadata
    try:
        metadata_file_path = Path(f"./update/autopts/data/v{version}/metadata.json")
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


@app.post("/autopts/update/modify", tags=["Auto PTS"])
def modify_update_info_base(update_info: UpdateInfo):
    file_path = Path("./update/autopts/update_info.json")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(update_info.dict(), f, ensure_ascii=False, indent=4)

    return {"message": "Update info modified successfully"}



############################################################################################################

@server_connection
def _search_label_info(tracking_id: str | None, conn=None) -> dict:
    try:
        if conn is None:
            return {
                "status": "internal_error",
                "message": "Connection to the database failed",
            }
        
        cur = conn.cursor()
        query = """
            SELECT scanned_info FROM label_info
            WHERE tracking_id = %s;
        """
        
        cur.execute(query, (tracking_id,))
        result = cur.fetchone()
        
        if result is None:
            return {
                "status": "not_found",
                "message": "Tracking ID not found",
            }
        else:
            return {
                "status": "success",
                "data": result[0],
            }
    except Exception as e:
        logger.error(f"Error occurred: {str(e)}", exc_info=True)
        return {
            "status": "internal_error",
            "message": f"An error occurred while processing the request: {str(e)}",
        }
    
    

@app.get("/aiotts/label", tags=["AIO TTS REST API"])
def search_label(
    tracking_id: str,
    api_key: str,
):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=401, detail="Invalid API Key"
        )
    if not isinstance(tracking_id, str):
        raise HTTPException(
            status_code=400, detail="Tracking ID must be a string"
        )
    
    result = _search_label_info(tracking_id)
    
    if result["status"] == "success":
        return JSONResponse(content=result)
    elif result["status"] == "not_found":
        raise HTTPException(status_code=404, detail="Tracking ID not found")
    else:
        raise HTTPException(status_code=500, detail=result["message"])
        