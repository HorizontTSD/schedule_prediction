from fastapi import APIRouter, Body, HTTPException

from src.services.schedule_predict_service import schedule_predict  # Импортируем из сервисного слоя

from src.core.logger import logger

router = APIRouter()

schedule_predict

@router.get("/")
async def func_schedule_predict():
    """
    Запускает прогноз по расписанию для всех заданных данных.

    Прогноз выполняется для всех компаний, для которых настроена генерация прогнозов.
    Все настройки берутся из конфигурации или базы данных.

    Возвращает статус выполнения задачи.
    """
    try:
        logger.info(f"Starting prediction schedule for all")
        report = await schedule_predict()
        logger.info("Prediction process completed successfully.")
        return report
    except Exception as ApplicationError:
        logger.error(f"Error occurred during prediction: {ApplicationError.__repr__()}")
        raise HTTPException(
            status_code=400,
            detail="Unknown Error",
            headers={"X-Error": f"{ApplicationError.__repr__()}"},
        )