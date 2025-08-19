import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), "test_db.sqlite")

if not os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        is_superuser INTEGER NOT NULL
    )
    """)
    conn.execute("INSERT INTO users (username, password, is_superuser) VALUES (?, ?, ?)",
                 ("admin", "admin_password", 1))
    conn.commit()
    conn.close()
    print("База и суперпользователь созданы:", db_path)
else:
    print("База уже существует:", db_path)
