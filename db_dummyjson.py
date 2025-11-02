import psycopg2
import os
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()

PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5432")
PG_DB = os.getenv("PG_DB", "fitbitdb")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "postgres")

def get_conn():
    return psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASSWORD
    )

@contextmanager
def db_cursor():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            yield cur
            conn.commit()
    except Exception as e:
        conn.rollback()
        print("❌ Erreur base de données :", e)
    finally:
        conn.close()

def insert_user(data):
    with db_cursor() as cur:
        cur.execute("""
            INSERT INTO dummy_users (
                first_name, last_name, age, gender, email, phone, blood_group,
                height, weight, eye_color, university, city, company_name,
                department, title, salary
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data["first_name"], data["last_name"], data["age"], data["gender"], data["email"],
            data["phone"], data["blood_group"], data["height"], data["weight"],
            data["eye_color"], data["university"], data["city"], data["company_name"],
            data["department"], data["title"], data["salary"]
        ))
