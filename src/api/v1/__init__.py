# src/api/v1/__init__.py
from fastapi import APIRouter

from src.api.v1.greeting import router as greeting_router

router = APIRouter()

router.include_router(greeting_router)
