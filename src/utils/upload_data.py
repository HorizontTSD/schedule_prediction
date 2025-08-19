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


async def upload_predict_to_db(credentials, func_create_client, response, destination_table, time_column, target_col):

    try:

        json_list_df_real_predict = response["map_data"]["data"]["predictions"]
        df_predict = pd.DataFrame(json_list_df_real_predict)
        df_predict_date = df_predict.copy()

        df_predict_date[time_column] = pd.to_datetime(df_predict_date[time_column])
        min_date = df_predict_date[time_column].min()

        conn = func_create_client(**credentials)
        cur = conn.cursor()

        query = f"""
        DELETE FROM {destination_table}
        WHERE datetime >= %s;
        """
        logger.info(f"OLD data was removed")

        cur.execute(query, (min_date,))

        data = [(row[time_column], row[target_col]) for _, row in df_predict.iterrows()]


        query = f"""
            INSERT INTO {destination_table} ({time_column}, {target_col})
            VALUES (%s, %s)
            ON CONFLICT ({time_column})
            DO UPDATE SET {target_col} = EXCLUDED.{target_col};
        """

        logger.info("Inserting forecasted data into the database.")
        cur.executemany(query, data)

        conn.commit()
        cur.close()
        conn.close()

        logger.info('Data successfully predicted and inserted into the database.')

        success = f'Was predicted and uploaded {len(df_predict)} lines'
        return success

    except Exception as e:
        logger.error(f"Error during prediction process: {e}")
        if conn:
            conn.rollback()
        raise e
