import os
import requests
import pandas as pd


from dotenv import load_dotenv
from src.core.logger import logger

load_dotenv()

home_path = os.getcwd()

url_backend = os.getenv("TOOL_BACKEND")

token = os.getenv("TOOL_BACKEND_TOKEN")


async def func_xgboost_generate_forecast(df: pd.DataFrame, time_column: str, col_target: str, forecast_horizon_time: str):

    url = f'{url_backend}/api/v1/predict-xgboost'

    df = df.copy()
    for col in df.select_dtypes(include=['datetime64[ns]']):
        df[col] = df[col].dt.strftime("%Y-%m-%d %H:%M:%S")
    df_records = df.to_dict(orient='records')

    data = {
        "df": df_records,
        "time_column": time_column,
        "col_target": col_target,
        "forecast_horizon_time": forecast_horizon_time,
        "lag_search_depth": 1
    }

    try:
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.post(url, json=data, headers=headers, timeout=1500)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Ошибка при запросе: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при запросе: {e}")
        return None
