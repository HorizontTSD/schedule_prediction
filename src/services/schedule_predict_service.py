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


async def schedule_predict():
    conn = test_get_db_connection()
    try:
        df_companies = pd.read_sql_query("SELECT * FROM organizations", conn)
        df_schedule_forecasting = pd.read_sql_query("SELECT * FROM schedule_forecasting", conn)
    except Exception as e:
        logger.error(f"DB query error: {e}")
        return {
            "report": {
                "errors": [{"company_id": None, "company_name": None, "status": "error", "info": str(e), "data_id": None, "data_name": None, "method_predict": None, "target_table": None, "target_db": None}],
                "success": []
            }
        }
    finally:
        conn.close()

    errors = []
    success = []

    for _, row_company in df_companies.iterrows():
        company_name = row_company["name"]
        company_id = row_company["id"]

        try:
            df_data_to_predict = df_schedule_forecasting[df_schedule_forecasting["organization_id"] == company_id]
        except Exception as e:
            logger.error(f"Filter error company {company_id}: {e}")
            errors.append({"company_id": company_id, "company_name": company_name, "status": "error", "info": str(e), "data_id": None, "data_name": None, "method_predict": None, "target_table": None, "target_db": None})
            continue

        for _, data_to_predict in df_data_to_predict.iterrows():
            try:
                data_id = data_to_predict["data_id"]
                data_name = data_to_predict["data_name"]
                connection_id = data_to_predict["connection_id"]
                source_table = data_to_predict["source_table"]
                time_column = data_to_predict["time_column"]
                target_column = data_to_predict["target_column"]
                discreteness = data_to_predict["discreteness"]
                target_db = data_to_predict["target_db"]
                count_time_points_predict = data_to_predict["count_time_points_predict"]
                methods_predict = json.loads(data_to_predict["methods_predict"])
            except Exception as e:
                logger.error(f"Row parse error company {company_id}: {e}")
                errors.append({"company_id": company_id, "company_name": company_name, "status": "error", "info": str(e), "data_id": None, "data_name": None, "method_predict": None, "target_table": None, "target_db": None})
                continue

            for method_predict in methods_predict:
                method = method_predict.get("method")
                target_table = method_predict.get("target_table")

                try:
                    df_last_values, credentials, func_create_client = await get_data(
                        company_id=company_id,
                        connection_id=connection_id,
                        table_name=source_table,
                        time_col=time_column,
                        target_col=target_column
                    )

                    forecast_horizon_time, df = await preprocess_last_values_data(
                        df_last_values=df_last_values,
                        time_col=time_column,
                        count_time_points_predict=count_time_points_predict,
                        time_interval=discreteness
                    )

                    if method == "XGBoost":
                        response = await func_xgboost_generate_forecast(
                            df=df,
                            time_column=time_column,
                            col_target=target_column,
                            forecast_horizon_time=forecast_horizon_time
                        )
                    else:
                        raise ValueError(f"Unknown method: {method}")

                    if target_db == "user":
                        credentials = credentials
                        func_create_client = func_create_client

                    success_result = await upload_predict_to_db(
                        credentials=credentials,
                        func_create_client=func_create_client,
                        response=response,
                        destination_table=target_table,
                        time_column=time_column,
                        target_col=target_column
                    )

                    success.append({
                        "company_id": company_id,
                        "company_name": company_name,
                        "status": "success",
                        "method_predict": method,
                        "info": str(success_result),
                        "data_id": data_id,
                        "data_name": data_name,
                        "target_table": target_table,
                        "target_db": target_db
                    })

                except Exception as e:
                    logger.error(f"Predict error company {company_id} data {data_id} method {method}: {e}")
                    errors.append({
                        "company_id": company_id,
                        "company_name": company_name,
                        "method_predict": method,
                        "status": "error",
                        "info": str(e),
                        "data_id": data_id,
                        "data_name": data_name,
                        "target_table": target_table,
                        "target_db": target_db
                    })

    return {"report": {"errors": errors, "success": success}}

async def main():
    await schedule_predict()

if __name__ == "__main__":
    asyncio.run(main())