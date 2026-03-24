import mysql.connector

from config import Config


def get_db_connection():
    return mysql.connector.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
    )


def query_db(sql, params=None, fetchone=False):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(sql, params or ())

    if fetchone:
        result = cursor.fetchone()
    else:
        result = cursor.fetchall()

    cursor.close()
    conn.close()
    return result


def execute_db(sql, params=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(sql, params or ())
    conn.commit()
    last_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return last_id
