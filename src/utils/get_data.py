from src.core.logger import logger
from src.clients.create_clients import get_db_connection
import pandas as pd
import os
import yaml
from dotenv import load_dotenv
load_dotenv()

db_connections_mapping = {
    1: get_db_connection,
}

home_path = os.getcwd()
path_to_yamls = os.path.join(home_path, "src", "info_for_predict")

path_to_yaml_db_connection_info = os.path.join(path_to_yamls, "connections_info.yaml")


async def get_data(company_id, table_name, time_col, target_col):
    try:
        with open(path_to_yaml_db_connection_info, "r") as f:
            connections_info = yaml.safe_load(f)
        company = connections_info[company_id]
        db_connections_id = company["db_connections_id"]

        credentials = company["credentials"]

        credentials["dbname"] = os.getenv("PG_DB")
        credentials["user"] = os.getenv("PG_USER")
        credentials["password"] = os.getenv("PG_PASSWORD")
        credentials["host"] = os.getenv("PG_HOST")
        credentials["port"] = os.getenv("PG_PORT")

        create_client = db_connections_mapping[db_connections_id]

        conn = create_client(**credentials)
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

        return df_last_values
        
    except Exception as e:
        logger.info(e)