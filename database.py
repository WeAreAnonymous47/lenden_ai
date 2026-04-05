# database.py

import pymysql

def get_db_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="0909BH0705VV0102HS",        # 🔴 change this
        database="school_management",
        cursorclass=pymysql.cursors.DictCursor
    )
