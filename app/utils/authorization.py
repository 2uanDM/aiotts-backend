# Authorize by API KEY
import os

from dotenv import load_dotenv
from fastapi import HTTPException, status

load_dotenv(override=True)


def validate_apikey(api_key: str):
    if os.getenv("MODE") == "development":
        return

    if api_key != os.getenv("API_KEY"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
