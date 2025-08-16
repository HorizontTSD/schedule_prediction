# src/api/__init__.py
from fastapi import APIRouter

from src.api.v1 import router as v1_router

api_router = APIRouter()

api_router.include_router(v1_router, prefix='/v1')
