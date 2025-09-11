import os
import asyncio
from typing import Any, Dict, List

import pandas as pd
from fastapi import HTTPException
from sqlalchemy import select, text
from datetime import datetime


from src.core.security.password import decrypt_password
from src.models.models import ScheduleForecasting, ConnectionSettings
from src.utils.xgboost_api_predict import func_xgboost_generate_forecast

from src.session import db_manager, DBManager
from dotenv import load_dotenv
from src.core.logger import logger


async def preprocess_last_values_data(df_last_values, time_col, count_time_points_predict, time_interval):
    try:
        df_last_values[time_col] = df_last_values[time_col].dt.tz_localize(None)

        df_last_values = df_last_values.sort_values(by=time_col, ascending=True)

        last_know_date = df_last_values[time_col].iloc[-1]
        logger.info(f"Last known date: {last_know_date}")

        datetime_range = pd.date_range(
            start=last_know_date,
            periods=count_time_points_predict,
            freq=f"{time_interval}s"
        ).floor("s")

        df = df_last_values

        forecast_horizon_time = datetime_range[-1].strftime("%Y-%m-%d %H:%M:%S")

        df[time_col] = pd.to_datetime(df[time_col])

        return forecast_horizon_time, df
    except:
        pass


load_dotenv()

home_path = os.getcwd()


async def get_all_forecast_configs_df() -> pd.DataFrame:
    async with db_manager.get_db_session() as session:
        stmt = select(ScheduleForecasting).where(
            ScheduleForecasting.is_deleted.is_not(True)
        )
        result = await session.execute(stmt)
        configs: List[ScheduleForecasting] = result.scalars().all()

        if not configs:
            raise HTTPException(status_code=404, detail="Настройки прогноза не найдены")

        data = [
            {k: v for k, v in cfg.__dict__.items() if not k.startswith("_")}
            for cfg in configs
        ]

        return pd.DataFrame(data)

async def get_connection_by_id_dict(connection_id: int) -> dict:
    async with db_manager.get_db_session() as session:
        stmt = select(ConnectionSettings).where(
            ConnectionSettings.id == connection_id,
            ConnectionSettings.is_deleted.is_not(True)
        )
        result = await session.execute(stmt)
        conn = result.scalars().first()

        if not conn:
            raise HTTPException(status_code=404, detail="Подключение не найдено")

        return {
            "connection_schema": conn.connection_schema,
            "db_name": conn.db_name,
            "host": conn.host,
            "port": conn.port,
            "db_user": conn.db_user,
            "db_password": decrypt_password(conn.db_password),
            "ssl": conn.ssl,
        }

async def ensure_tables_exist(
        methods_predict: list[dict],
        target_db_manager,
        time_column: str,
        target_column: str
) -> bool:
    async with target_db_manager.get_db_session() as session:
        for method_dict in methods_predict:
            table_name = method_dict.get("target_table")
            table_name_safe = f'"{table_name}"'

            query_exists = text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = '{table_name.lower()}'
                );
            """)
            result = await session.execute(query_exists)
            exists = result.scalar()

            if exists:
                query_columns = text(f"""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name = '{table_name.lower()}';
                """)
                result = await session.execute(query_columns)
                columns = [row[0] for row in result.fetchall()]
                if time_column in columns and target_column in columns:
                    continue  # Таблица есть и колонки правильные — пропускаем
                else:
                    drop_query = text(f'DROP TABLE IF EXISTS {table_name_safe};')
                    await session.execute(drop_query)
                    await session.commit()

            create_query = text(f"""
                CREATE TABLE {table_name_safe} (
                    id SERIAL PRIMARY KEY,
                    {time_column} TIMESTAMP UNIQUE,
                    {target_column} DOUBLE PRECISION
                );
            """)
            try:
                await session.execute(create_query)
                await session.commit()
            except Exception as e:
                print(f"Не удалось создать таблицу {table_name}: {e}")
                return False
    return True



async def get_table_data_df(table_name: str, source_db_manager) -> pd.DataFrame:
    async with source_db_manager.get_db_session() as session:
        table_name_safe = f'"{table_name}"'
        query = text(f'SELECT * FROM {table_name_safe};')
        try:
            result = await session.execute(query)
            rows = result.mappings().all()
            return pd.DataFrame(rows)
        except Exception as e:
            return pd.DataFrame()


async def schedule_predict():
    df = await get_all_forecast_configs_df()
    for index, row in df.iterrows():
        connection_id = row.connection_id
        target_db = row.target_db
        connection = await get_connection_by_id_dict(connection_id=connection_id)
        methods_predict = row.methods_predict

        if connection["connection_schema"] == "PostgreSQL":
            source_url_db = f"postgresql+asyncpg://{connection['db_user']}:{connection['db_password']}@{connection['host']}:{connection['port']}/{connection['db_name']}"
            source_db_manager = DBManager(source_url_db)
        else:
            continue

        if target_db == "self_host" and connection["connection_schema"] == "PostgreSQL":
            target_db_manager = source_db_manager
        else:
            target_db_manager = db_manager

        tables_ok = await ensure_tables_exist(methods_predict, target_db_manager)
        if not tables_ok:
            continue

async def insert_predict_to_table(df: pd.DataFrame, target_table: str, target_db_manager, time_column: str, target_column: str):
    if df.empty:
        return

    async with target_db_manager.get_db_session() as session:
        table_name_safe = f'"{target_table}"'
        for row in df.itertuples(index=False):
            time_value = row[0]
            if isinstance(time_value, str):
                time_value = datetime.fromisoformat(time_value)

            query = text(f"""
                INSERT INTO {table_name_safe} ({time_column}, {target_column})
                VALUES (:time_value, :target_value)
                ON CONFLICT ({time_column})
                DO UPDATE SET {target_column} = EXCLUDED.{target_column};
            """)
            await session.execute(query, {"time_value": time_value, "target_value": row[1]})
        await session.commit()


async def schedule_predict_v2():
    df = await get_all_forecast_configs_df()
    logs = {}

    for index, row in df.iterrows():
        connection_id = row.connection_id
        target_db = row.target_db
        methods_predict = row.methods_predict
        discreteness = row.discreteness
        count_time_points_predict = row.count_time_points_predict
        source_table = row.source_table
        time_column = row.time_column
        target_column = row.target_column

        if connection_id not in logs:
            logs[connection_id] = {"report": {"errors": [], "success": []}}

        try:
            connection = await get_connection_by_id_dict(connection_id=connection_id)
        except Exception as e:
            logs[connection_id]["report"]["errors"].append({
                "connection_id": connection_id,
                "status": "error",
                "info": str(e),
                "methods_predict": None,
                "target_table": None,
                "target_db": target_db
            })
            continue

        try:
            if connection["connection_schema"] == "PostgreSQL":
                source_url_db = f"postgresql+asyncpg://{connection['db_user']}:{connection['db_password']}@{connection['host']}:{connection['port']}/{connection['db_name']}"
                source_db_manager = DBManager(source_url_db)
            else:
                raise ValueError(f"Подключение со схемой {connection['connection_schema']} не поддерживается")
        except Exception as e:
            logs[connection_id]["report"]["errors"].append({
                "connection_id": connection_id,
                "status": "error",
                "info": str(e),
                "methods_predict": None,
                "target_table": None,
                "target_db": target_db
            })
            continue

        if target_db == "self_host" and connection["connection_schema"] == "PostgreSQL":
            target_db_manager = source_db_manager
        else:
            target_db_manager = db_manager

        tables_ok = await ensure_tables_exist(
            methods_predict=methods_predict,
            target_db_manager=target_db_manager,
            time_column=time_column,
            target_column=target_column
        )
        if not tables_ok:
            logs[connection_id]["report"]["errors"].append({
                "connection_id": connection_id,
                "status": "error",
                "info": "Нет таблицы и не смогли её создать",
                "methods_predict": None,
                "target_table": None,
                "target_db": target_db
            })
            continue

        try:
            df_data = await get_table_data_df(table_name=source_table, source_db_manager=source_db_manager)
            forecast_horizon_time, df_for_predict = await preprocess_last_values_data(
                df_last_values=df_data,
                time_col=time_column,
                count_time_points_predict=count_time_points_predict,
                time_interval=discreteness
            )
        except Exception as e:
            logs[connection_id]["report"]["errors"].append({
                "connection_id": connection_id,
                "status": "error",
                "info": f"Ошибка предобработки данных: {e}",
                "methods_predict": None,
                "target_table": None,
                "target_db": target_db
            })
            continue

        for method_predict in methods_predict:
            method = method_predict.get("method")
            target_table = method_predict.get("target_table")

            try:
                if method == "XGBoost":
                    response = await func_xgboost_generate_forecast(
                        df=df_for_predict,
                        time_column=time_column,
                        col_target=target_column,
                        forecast_horizon_time=forecast_horizon_time
                    )
                else:
                    raise ValueError(f"Unknown predict method: {method}")

                preds = response['map_data']['data']['predictions']
                df_preds = pd.DataFrame(preds)[[time_column, target_column]]

                await insert_predict_to_table(
                    df=df_preds,
                    target_table=target_table,
                    target_db_manager=target_db_manager,
                    time_column=time_column,
                    target_column=target_column
                )

                logs[connection_id]["report"]["success"].append({
                    "connection_id": connection_id,
                    "status": "success",
                    "info": f"Прогноз успешно записан в {target_table}",
                    "methods_predict": method,
                    "target_table": target_table,
                    "target_db": target_db
                })

            except Exception as e:
                logs[connection_id]["report"]["errors"].append({
                    "connection_id": connection_id,
                    "status": "error",
                    "info": str(e),
                    "methods_predict": method,
                    "target_table": target_table,
                    "target_db": target_db
                })

    return logs


async def main():
    logs = await schedule_predict()
    print(logs)

if __name__ == "__main__":
    asyncio.run(main())