import os
import json

from src.utils.get_data import get_data
from src.utils.upload_data import upload_predict_to_db

from src.utils.preprocess import preprocess_last_values_data
import asyncio
from src.utils.xgboost_api_predict import func_xgboost_generate_forecast

from dotenv import load_dotenv
from src.core.logger import logger
from src.db_scripts.test_db_area.test_client import test_get_db_connection
import pandas as pd


load_dotenv()

home_path = os.getcwd()

path_to_yamls = os.path.join(home_path, "src", "info_for_predict")


async def schedule_predict():

    conn = test_get_db_connection()

    query_companies = "SELECT * FROM organizations"
    df_companies = pd.read_sql_query(query_companies, conn)

    query_schedule_forecasting = "SELECT * FROM schedule_forecasting"
    df_schedule_forecasting = pd.read_sql_query(query_schedule_forecasting, conn)

    conn.close()

    for index, row_company in  df_companies.iterrows():
        company_name = row_company["name"]
        company_id = row_company["id"]
        df_data_to_predict = df_schedule_forecasting[df_schedule_forecasting["organization_id"] == company_id]

        for index, data_to_predict in df_data_to_predict.iterrows():
            data_id = data_to_predict["data_id"]
            data_name = data_to_predict["data_name"]
            connection_id = data_to_predict["connection_id"]

            print(f"connection_id = {connection_id}")

            source_table = data_to_predict["source_table"]
            time_column = data_to_predict["time_column"]
            target_column = data_to_predict["target_column"]
            discreteness = data_to_predict["discreteness"]
            target_db = data_to_predict["target_db"]
            count_time_points_predict = data_to_predict["count_time_points_predict"]
            # methods_predict = data_to_predict["methods_predict"]
            methods_predict = json.loads(data_to_predict["methods_predict"])

            df_last_values, credentials, func_create_client = await get_data(
                company_id=company_id,
                connection_id=connection_id,
                table_name=source_table,
                time_col=time_column,
                target_col=target_column)

            forecast_horizon_time, df = await preprocess_last_values_data(
                df_last_values=df_last_values,
                time_col=time_column,
                count_time_points_predict=count_time_points_predict,
                time_interval=discreteness
                )

            for method_predict in methods_predict:
                method = method_predict["method"]
                target_table = method_predict["target_table"]

                if method == "XGBoost":
                    response = await func_xgboost_generate_forecast(
                        df=df,
                        time_column=time_column,
                        col_target=target_column,
                        forecast_horizon_time=forecast_horizon_time)
                elif method == "XGBoost":
                    pass

                if target_db == "user": # Если они сохраняют к нам то меняем загрузку данных на наше соеденение
                    credentials=credentials # В данном случае оно одно и тоже тк тестовые данные
                    func_create_client=func_create_client

                success = await upload_predict_to_db(
                    credentials=credentials,
                    func_create_client=func_create_client,
                    response=response,
                    destination_table=target_table,
                    time_column=time_column,
                    target_col=target_column
                )
                logger.info(success)



async def main():
    await schedule_predict()

if __name__ == "__main__":
    asyncio.run(main())