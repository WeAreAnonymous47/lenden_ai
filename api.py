# api.py
from database import get_db_connection
from google import genai
import csv

# GET all students
def fetch_db_student():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM students")
            return cursor.fetchall()
    finally:
        conn.close()


# GET all students
# def fetch_report2():
#     conn = get_db_connection()
#     try:
#         with conn.cursor() as cursor:
#             cursor.execute("SELECT * FROM p2p")
#             return cursor.fetchall()
#     finally:
#         conn.close()


def fetch_report():

    report_data = []

    try:
        with open("report.csv", mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for row in reader:
                report_data.append(row)

        return report_data

    except Exception as e:
        print("CSV read error:", e)
        return []

# print(fetch_report2())

# POST - create student
def create_student(data: dict):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO students
                (admission_no, first_name, last_name, date_of_birth, gender, phone, email)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                data["admission_no"],
                data["first_name"],
                data["last_name"],
                data["date_of_birth"],
                data["gender"],
                data["phone"],
                data["email"],
            ))
            conn.commit()
            return cursor.lastrowid
    finally:
        conn.close()


def gemini_prompt(prompt: dict):
    GEMINI_API_KEY = "AIzaSyCiCwrQA9An1aSFFPhXJRQ3kR7FI4xA8wI"
    client = genai.Client(api_key=GEMINI_API_KEY)

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=prompt["prompt"],
    )

    return response.text


# PUT - update student
def update_student(student_id: int, data: dict):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                UPDATE students
                SET first_name=%s, last_name=%s, phone=%s, email=%s
                WHERE id=%s
            """
            cursor.execute(sql, (
                data["first_name"],
                data["last_name"],
                data["phone"],
                data["email"],
                student_id
            ))
            conn.commit()
            return cursor.rowcount
    finally:
        conn.close()


# DELETE - delete student
def delete_student(student_id: int):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "DELETE FROM students WHERE id=%s",
                (student_id,)
            )
            conn.commit()
            return cursor.rowcount
    finally:
        conn.close()


