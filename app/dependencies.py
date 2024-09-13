import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import Header, HTTPException

load_dotenv()

API_AUTHENTICATION_KEY = os.getenv("API_AUTHENTICATION_KEY")


def authenticate(x_api_key: Optional[str] = Header(None)) -> None:
    if x_api_key != API_AUTHENTICATION_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")
