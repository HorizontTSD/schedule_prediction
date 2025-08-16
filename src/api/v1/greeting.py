# src/api/v1/greeting.py
from typing import Annotated

from fastapi import APIRouter, Body, HTTPException

from src.models import HellowRequest
from src.services.greeting_service import greet_users  # Импортируем из сервисного слоя

# from src.core.logger import logger

router = APIRouter()

@router.post("/greetings")
async def inputation(
    body: Annotated[
        HellowRequest,
        Body(example={"names": ["Sasha", "Nikita", "Kristina"]}),
    ]
):
    try:
        names = body.names
        if names:
            # Вызываем сервисную функцию
            res = greet_users(names)
            return res
        else:
            # logger.error("Names list is empty")
            raise HTTPException(
                status_code=400,
                detail="Bad Request",
                headers={"X-Error": "Names list is empty"},
            )
    except Exception as application_error:
        # logger.error(application_error.__repr__())
        raise HTTPException(
            status_code=400,
            detail="Unknown Error",
            headers={"X-Error": f"{application_error.__repr__()}"},
        )

# GET-ручкА для проверки
@router.get("/")
def read_root():
    return {"message": "Welcome to the Greeting API v1"}
