import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5432")
PG_DB = os.getenv("PG_DB", "fitbitdb")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "postgres")

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS dummy_users (
    id SERIAL PRIMARY KEY,
    first_name TEXT,
    last_name TEXT,
    age INT,
    gender TEXT,
    email TEXT,
    phone TEXT,
    blood_group TEXT,
    height FLOAT,
    weight FLOAT,
    eye_color TEXT,
    university TEXT,
    city TEXT,
    company_name TEXT,
    department TEXT,
    title TEXT,
    salary FLOAT
);
"""

def create_table():
    conn = psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASSWORD
    )
    cur = conn.cursor()
    cur.execute(CREATE_TABLE_SQL)
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Table enrichie dummy_users créée avec succès !")

if __name__ == "__main__":
    create_table()
