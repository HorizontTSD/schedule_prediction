import os

import yaml

from src.utils.get_data import get_data
from src.utils.upload_data import upload_predict_to_db

from src.utils.preprocess import preprocess_last_values_data
import asyncio
from src.utils.xgboost_api_predict import func_xgboost_generate_forecast

from dotenv import load_dotenv
from src.core.logger import logger

load_dotenv()

home_path = os.getcwd()

path_to_yamls = os.path.join(home_path, "src", "info_for_predict")

path_to_yaml_forecast_schemas = os.path.join(path_to_yamls, "forecast_schemas.yaml")
path_to_yaml_db_connection_info = os.path.join(path_to_yamls, "connections_info.yaml")


async def schedule_predict():

    with open(path_to_yaml_forecast_schemas, "r") as f:
        forecast_schemas = yaml.safe_load(f)

    for company in  forecast_schemas:
        company_name = company["company_name"]
        company_id = company["company_id"]
        data_to_predict_list = company["data_to_predict"]

        for data_to_predict in data_to_predict_list:
            data_id = data_to_predict["data_id"]
            data_name = data_to_predict["data_name"]
            source_table = data_to_predict["source_table"]
            time_column = data_to_predict["time_column"]
            target_column = data_to_predict["target_column"]
            discreteness = data_to_predict["discreteness"]
            target_db = data_to_predict["target_db"]
            count_time_points_predict = data_to_predict["count_time_points_predict"]
            methods_predict = data_to_predict["methods_predict"]

            df_last_values = await get_data(
                company_id=company_id,
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

                success = await upload_predict_to_db(
                    company_id=company_id,
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