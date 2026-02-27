PG_DB=ats_db
PG_USER=ats_user
PG_PASSWORD=Ats1320!
PG_HOST=95.165.85.82
PG_PORT=8501


import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

dbname = os.getenv("PG_DB")
user = os.getenv("PG_USER")
password = os.getenv("PG_PASSWORD")
host = os.getenv("PG_HOST")
port = os.getenv("PG_PORT")

def get_db_connection():
    return psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port,
    )