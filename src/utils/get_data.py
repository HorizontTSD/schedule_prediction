from src.core.logger import logger
from src.clients.create_clients import get_db_connection
import pandas as pd
import os
from dotenv import load_dotenv
from src.db_scripts.test_db_area.test_client import test_get_db_connection

load_dotenv()

db_connections_mapping = {
    "TimescaleDB": get_db_connection,
}

home_path = os.getcwd()
path_to_yamls = os.path.join(home_path, "src", "info_for_predict")

path_to_yaml_db_connection_info = os.path.join(path_to_yamls, "connections_info.yaml")


async def get_data(company_id, connection_id, table_name, time_col, target_col):
    try:
        conn = test_get_db_connection()

        query = f"""
            SELECT *
            FROM connection_settings
            WHERE organization_id = ?
              AND id = ?
        """
        df_connection_settings = pd.read_sql_query(query, conn, params=(company_id, connection_id))
        conn.close()
        print(df_connection_settings)
        db_connections_schema_id = df_connection_settings["connection_schema"].values[0]

        credentials = {
            "dbname": df_connection_settings["db_name"].values[0],
            "user": df_connection_settings["db_user"].values[0],
            "password": df_connection_settings["db_password"].values[0],
            "host": df_connection_settings["host"].values[0],
            "port": df_connection_settings["port"].values[0],
        }

        func_create_client = db_connections_mapping[db_connections_schema_id]

        conn = func_create_client(**credentials)
        cur = conn.cursor()

        select_query = f"""
                SELECT * FROM {table_name} ORDER BY datetime DESC;
                """

        logger.info(f"Executing SQL query: {select_query}")
        cur.execute(select_query)
        rows = cur.fetchall()

        conn.commit()
        cur.close()
        conn.close()

        if not rows:
            logger.error("No data retrieved from the database.")
            raise ValueError("No data retrieved from the database.")

        logger.info("Transforming data into DataFrame.")
        df_last_values = pd.DataFrame(rows, columns=[time_col, target_col])

        return df_last_values, credentials, func_create_client
        
    except Exception as e:
        logger.info(e)