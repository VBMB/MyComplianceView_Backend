import pymysql
from pymysql.cursors import DictCursor

def get_db_connection():
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='',
        database='mcv',
        port=3306,
        cursorclass=DictCursor

    )
    return connection
