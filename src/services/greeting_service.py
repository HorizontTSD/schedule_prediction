# src/services/greeting_service.py
"""
Сервисный слой для обработки логики приветствий.
Перенос логики из src/utils/greeting.py.
"""

# from src.core.logger import logger

def greet_users(names: list[str]) -> list[str]:
    """
    Генерирует список приветствий для заданных имён.

    Args:
        names (list[str]): Список имён для приветствия.

    Returns:
        list[str]: Список строк с приветствиями в формате "Hello {name}!".
    """
    # logger.info(f"Generating greetings for {len(names)} names.")
    greetings = [f"Hello {name}!" for name in names]
    # logger.info("Greetings generated successfully.")
    return greetings
