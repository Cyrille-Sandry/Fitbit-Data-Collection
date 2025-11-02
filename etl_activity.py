import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

load_dotenv()

def load_activity_data(start_date=None, end_date=None, user_id=None):
    """
    Charge les données dailyActivity depuis PostgreSQL avec filtres optionnels.
    """
    conn = psycopg2.connect(
        host=os.getenv("PG_HOST", "localhost"),
        dbname=os.getenv("PG_DB", "fitbit_db"),
        user=os.getenv("PG_USER", "postgres"),
        password=os.getenv("PG_PASSWORD", "password"),
        port=os.getenv("PG_PORT", 5432)
    )

    # 🧩 Plage par défaut réaliste pour le dataset Kaggle
    default_start = "2016-03-01"
    default_end   = "2016-06-30"

    if not start_date:
        start_date = default_start
    if not end_date:
        end_date = default_end


    query = """
        SELECT id, activity_date, total_steps, total_distance, calories,
               very_active_minutes, fairly_active_minutes, lightly_active_minutes, sedentary_minutes
        FROM fitbit_daily_activity
        WHERE activity_date BETWEEN %s AND %s
    """

    params = [start_date, end_date]
    if user_id:
        query += " AND id = %s"
        params.append(user_id)
 #   if start_date:
 #       query += " AND activity_date >= %s"
 #       params.append(start_date)
 #   if end_date:
 #       query += " AND activity_date <= %s"
 #       params.append(end_date)

    query += " ORDER BY id, activity_date"

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, params)
        rows = cur.fetchall()

    conn.close()
    return pd.DataFrame(rows)
