import psycopg2
from config import DB_NAME, DB_USER, DB_PASSWORD, DB_HOST

def connect():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
