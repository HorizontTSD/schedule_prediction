import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_db_connection(dbname, user, password, host, port):
    return psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port,
    )

