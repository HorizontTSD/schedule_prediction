from src.db_scripts.test_db_area.test_client import test_get_db_connection
import json
import os
from dotenv import load_dotenv

load_dotenv()

conn = test_get_db_connection()
cursor = conn.cursor()

try:
    cursor.execute("""
        INSERT INTO organizations (id, name, email)
        VALUES (?, ?, ?)
    """, (1, "University of Brescia", "info@unibs.it"))
    print("✅ organizations вставлено")
except Exception as e:
    print("❌ organizations ошибка:", e)

try:
    cursor.execute("""
        INSERT INTO connection_settings (
            id, organization_id, connection_schema, db_name, host, port, ssl, db_user, db_password
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        1, 1, "TimescaleDB", os.getenv("PG_DB"),
        os.getenv("PG_HOST"), int(os.getenv("PG_PORT")), 1,
        os.getenv("PG_USER"), os.getenv("PG_PASSWORD")
    ))
    print("✅ connection_settings вставлено")
except Exception as e:
    print("❌ connection_settings ошибка:", e)

try:
    methods_predict = json.dumps([
        {"method": "XGBoost", "target_table": "xgb_predict_load_consumption"},
        {"method": "LSTM", "target_table": "predict_load_consumption"}
    ])

    cursor.execute("""
        INSERT INTO schedule_forecasting (
            id, organization_id, connection_id, data_id, data_name, source_table,
            time_column, target_column, discreteness, count_time_points_predict,
            target_db, methods_predict
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        1, 1, 1, 1, "Italy Electricity Consumption",
        "load_consumption", "Datetime", "load_consumption",
        300, 288, "user", methods_predict
    ))
    print("✅ schedule_forecasting вставлено")
except Exception as e:
    print("❌ schedule_forecasting ошибка:", e)

try:
    cursor.execute("""
        INSERT INTO organization_access (id, organization_id, access_level, max_users, max_forecasts, max_connections)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (1, 1, "basic", 10, 5, 3))
    print("✅ organization_access вставлено")
except Exception as e:
    print("❌ organization_access ошибка:", e)

conn.commit()
conn.close()
print("🎉 Все операции завершены")
