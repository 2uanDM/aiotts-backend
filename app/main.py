import json
import logging
import os
from pathlib import Path

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

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
def download_installer():
    file_path = Path("./uploads/AIO TikTokShop V2.rar")

    # Print the file path as the logger and return the file
    logger.info(f"Requested file path: {file_path}")

    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        raise HTTPException(
            status_code=404, detail="File AIO TikTokShop V2.rar not found"
        )

    return FileResponse(
        file_path,
        media_type="application/octet-stream",
        filename="AIO TikTokShop V2.rar",
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


######################################
DEV_ENDPOINT = os.getenv("DEV_FLASHSHIP_ENDPOINT")
PROD_ENDPOINT = os.getenv("PROD_FLASHSHIP_ENDPOINT")


def get_flashship_header(auth: bool = False, access_token: str | None = None) -> dict:
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "vi,en-US;q=0.9,en;q=0.8,vi-VN;q=0.7",
        "access-control-allow-origin": "*",
        "origin": "https://devpod.flashship.net",
        "priority": "u=1, i",
        "referer": "https://devpod.flashship.net/upload-orders",
        "sec-ch-ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    }

    if auth:
        headers["authorization"] = f"Bearer {access_token}"

    return headers


##### login #####
class LoginBody(BaseModel):
    api_key: str
    username: str
    password: str


@app.post("/flashship/login", tags=["FlashShip"])
def login(body: LoginBody, mode: str):
    api_key = body.api_key
    if not api_key or api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    if mode == "dev":
        endpoint = DEV_ENDPOINT
    elif mode == "prod":
        endpoint = PROD_ENDPOINT
    else:
        raise HTTPException(status_code=400, detail="Invalid mode")

    # Use the endpoint variable to construct the URL
    url = f"{endpoint}/seller-api-v2/token"

    print("==>> url:", url)

    try:
        response = requests.post(
            url=url,
            json={"username": body.username, "password": body.password},
            headers=get_flashship_header(),
        )
    except Exception as e:
        logger.error("Error while logging in:", exc_info=True)
        return JSONResponse(
            content={"msg": "fail", "error": str(e)},
            status_code=500,
        )

    status_code = response.status_code
    print(f"==>> login status_code: {status_code}")

    if response.json().get("msg") == "fail":
        status_code = 401

    return JSONResponse(
        content=response.json(),
        status_code=status_code,
    )


##### Create orders #####
class OrderBody(BaseModel):
    variant_id: int
    printer_design_front_url: str
    printer_design_back_url: str | None
    printer_design_right_url: str | None
    printer_design_left_url: str | None
    printer_design_neck_url: str | None
    mockup_front_url: None
    mockup_back_url: None
    mockup_right_url: None
    mockup_left_url: None
    mockup_neck_url: None
    quantity: int
    note: str


class OrderItem(BaseModel):
    access_token: str
    api_key: str
    order_id: str
    buyer_first_name: str
    buyer_last_name: str
    buyer_email: str
    buyer_phone: str
    buyer_address1: str
    buyer_address2: str
    buyer_city: str
    buyer_province_code: str
    buyer_zip: str
    buyer_country_code: str
    shipment: str
    link_label: str
    products: list[OrderBody]


@app.post("/flashship/order/create", tags=["FlashShip"])
def create_order(body: OrderItem, mode: str):
    api_key = body.api_key
    if not api_key or api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    if mode == "dev":
        endpoint = DEV_ENDPOINT
    elif mode == "prod":
        endpoint = PROD_ENDPOINT
    else:
        raise HTTPException(status_code=400, detail="Invalid mode")

    # Use the endpoint variable to construct the URL
    url = f"{endpoint}/seller-api-v2/orders/shirt-add"
    print("==>> url:", url)

    try:
        response = requests.post(
            url=url,
            json=body.model_dump(),
            headers=get_flashship_header(auth=True, access_token=body.access_token),
        )
    except Exception as e:
        logger.error("Error while creating order:", exc_info=True)
        return JSONResponse(
            content={"msg": "fail", "error": str(e)},
            status_code=500,
        )

    status_code = response.status_code

    return JSONResponse(
        content=response.json(),
        status_code=status_code,
    )
