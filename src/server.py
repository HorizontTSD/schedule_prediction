# src/server.py
import logging

# import pandas as pd
import uvicorn
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import api_router
from src.core.configuration.config import settings
from src.core.token import token_validator

logger = logging.getLogger(__name__)

app = FastAPI(
    docs_url="/template_fast_api/v1/",
    openapi_url='/template_fast_api/v1/openapi.json',
    dependencies=[Depends(token_validator)] if settings.VERIFY_TOKEN else []
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_origins_urls(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    api_router, prefix='/api'
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the indicators System API"}


if __name__ == "__main__":
    try:
        logger.info(f"Starting server on http://{settings.HOST}:{settings.PORT}")
        uvicorn.run(
            "server:app",
            host=settings.HOST,
            port=settings.PORT,
            workers=4,
            log_level="debug",
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")