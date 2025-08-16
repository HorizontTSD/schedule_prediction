import pandas as pd
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
            freq=f"{time_interval}S"
        ).floor("S")

        df = df_last_values

        forecast_horizon_time = datetime_range[-1].strftime("%Y-%m-%d %H:%M:%S")

        df[time_col] = pd.to_datetime(df[time_col])

        return forecast_horizon_time, df
    except:
        pass
