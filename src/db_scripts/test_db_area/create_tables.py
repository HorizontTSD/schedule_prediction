from src.db_scripts.test_db_area.test_client import test_get_db_connection

conn = test_get_db_connection()
cursor = conn.cursor()

tables = {
    "organizations": """
        CREATE TABLE organizations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            email TEXT UNIQUE NOT NULL
        )
    """,
    "users": """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            organization_id INTEGER NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            email TEXT UNIQUE NOT NULL,
            nickname TEXT UNIQUE,
            password TEXT NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            last_activity DATETIME,
            is_active BOOLEAN NOT NULL DEFAULT 1,
            is_blocked BOOLEAN NOT NULL DEFAULT 0,
            is_deleted BOOLEAN NOT NULL DEFAULT 0,
            FOREIGN KEY (organization_id) REFERENCES organizations(id)
        )
    """,
    "connection_settings": """
        CREATE TABLE connection_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            organization_id INTEGER NOT NULL,
            connection_schema TEXT NOT NULL,
            db_name TEXT NOT NULL,
            host TEXT NOT NULL,
            port INTEGER NOT NULL DEFAULT 5432,
            ssl BOOLEAN NOT NULL DEFAULT 1,
            db_user TEXT NOT NULL,
            db_password TEXT NOT NULL,
            FOREIGN KEY (organization_id) REFERENCES organizations(id)
        )
    """,
    "schedule_forecasting": """
        CREATE TABLE schedule_forecasting (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            organization_id INTEGER NOT NULL,
            connection_id INTEGER NOT NULL,
            data_id INTEGER NOT NULL,
            data_name TEXT NOT NULL,
            source_table TEXT NOT NULL,
            time_column TEXT NOT NULL,
            target_column TEXT NOT NULL,
            discreteness INTEGER NOT NULL,
            count_time_points_predict INTEGER NOT NULL,
            target_db TEXT NOT NULL DEFAULT 'self_host',
            methods_predict TEXT NOT NULL,
            FOREIGN KEY (organization_id) REFERENCES organizations(id)
        )
    """,
    "organization_access": """
        CREATE TABLE organization_access (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            organization_id INTEGER NOT NULL,
            access_level TEXT NOT NULL DEFAULT 'basic',
            max_users INTEGER NOT NULL DEFAULT 10,
            max_forecasts INTEGER NOT NULL DEFAULT 5,
            max_connections INTEGER NOT NULL DEFAULT 3,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN NOT NULL DEFAULT 1,
            FOREIGN KEY (organization_id) REFERENCES organizations(id)
        )
    """
}

for table_name, ddl in tables.items():
    cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
    print("="*75)
    print(f"Таблица '{table_name}' удалена (если существовала)")
    cursor.execute(ddl)
    print(f"Таблица '{table_name}' создана")

conn.commit()
conn.close()
