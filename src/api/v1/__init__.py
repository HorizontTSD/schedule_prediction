# src/api/v1/__init__.py
from fastapi import APIRouter

from src.api.v1.schedule_predict import router as func_schedule_predict

router = APIRouter()


router.include_router(func_schedule_predict, prefix="/run_schedule_predict", tags=["Run Sschedule Predict"] )
