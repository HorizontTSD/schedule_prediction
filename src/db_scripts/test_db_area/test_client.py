import os
import sqlite3
from dotenv import load_dotenv

load_dotenv()

home_path = os.getcwd()

test_db_path = os.path.join(home_path, "src", "db_scripts", "test_db_area", "test_db.sqlite")

def test_get_db_connection(db_path=None):
    if db_path is None:
        db_path = os.getenv("SQLITE_DB_PATH", test_db_path)
    return sqlite3.connect(db_path)
