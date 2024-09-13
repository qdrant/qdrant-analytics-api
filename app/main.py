from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.dependencies import authenticate
from app.routers import tracking
from app.utils import get_allowed_origins

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tracking.router)


@app.get("/")
async def root(api_key: str = Depends(authenticate)):
    return {"message": "Welcome to the Qdrant Tracking API"}
