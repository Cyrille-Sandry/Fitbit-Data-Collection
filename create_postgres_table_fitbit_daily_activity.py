import os
import pandas as pd
import numpy as np
import psycopg2
from psycopg2 import sql


########################################
####### CONFIGURATION 
########################################

CSV_PATH = r"data\dailyActivity_merged.csv"  # Absolute path to your CSV
# Paramètres de connexion PostgreSQL
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5432")
PG_DB = os.getenv("PG_DB", "fitbitdb")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "postgres")

# LOAD CSV 

try:
    df = pd.read_csv("data\dailyActivity_merged.csv")
    print("✅ CSV loaded successfully!")
except FileNotFoundError:
    raise FileNotFoundError(f"❌ CSV file not found at path: {CSV_PATH}")

##########################################
########   CLEANING & NORMALIZATION ######
##########################################


# Normalize column names
import re

def clean_column(col):
    col = re.sub(r'(?<!^)(?=[A-Z])', '_', col).lower()      # camel→snake (?<!^): “Only match if it’s not at the start of the string” -- 
                                                            # (?=[A-Z]): “Find every position before an uppercase letter (A–Z)”

    col = col.replace(' ', '_')                             # spaces→underscores
    return col.strip('_')

df.columns = [clean_column(c) for c in df.columns]

# Fix date column name depending on source

if 'activity_date' in df.columns:
    df['activity_date'] = pd.to_datetime(df['activity_date'])
elif 'activitydate' in df.columns:
    df['activity_date'] = pd.to_datetime(df['activitydate'])
else:
    raise KeyError("❌ No 'activity_date' or 'activityDate' column found in CSV")

# Fill numeric NaNs with 0
numeric_cols = df.select_dtypes(include=[np.number]).columns
df[numeric_cols] = df[numeric_cols].fillna(0)

# Remove duplicates and replace NaN with None for PostgreSQL
df = df.drop_duplicates(subset=['id', 'activity_date']).replace({np.nan: None})

print(f"✅ Cleaned dataset: {len(df)} rows, {len(df.columns)} columns")


#############################################
########### CONNECT TO POSTGRESQL 
#############################################

try:
    conn = psycopg2.connect(
        dbname=PG_DB,
        user=PG_DB,
        password=PG_PASSWORD,
        host=PG_HOST,
        port=PG_PORT
    )
    cur = conn.cursor()
    print("✅ Connected to PostgreSQL successfully!")
except Exception as e:
    raise ConnectionError(f"❌ PostgreSQL connection failed: {e}")


################################################
######## CREATE TABLE IF NOT EXISTS 
################################################

create_table_query = """
CREATE TABLE IF NOT EXISTS fitbit_daily_activity (
    id BIGINT,
    activity_date DATE,
    total_steps INT,
    total_distance FLOAT,
    tracker_distance FLOAT,
    logged_activities_distance FLOAT,
    very_active_distance FLOAT,
    moderately_active_distance FLOAT,
    light_active_distance FLOAT,
    sedentary_active_distance FLOAT,
    very_active_minutes INT,
    fairly_active_minutes INT,
    lightly_active_minutes INT,
    sedentary_minutes INT,
    calories INT,
    PRIMARY KEY (id, activity_date)
);
"""
cur.execute(create_table_query)
conn.commit()
print("✅ Table 'fitbit_daily_activity' created or verified.")


########################################
####### INSERT DATA 
########################################


columns = [
    'id', 'activity_date', 'total_steps', 'total_distance',
    'tracker_distance', 'logged_activities_distance',
    'very_active_distance', 'moderately_active_distance',
    'light_active_distance', 'sedentary_active_distance',
    'very_active_minutes', 'fairly_active_minutes',
    'lightly_active_minutes', 'sedentary_minutes', 'calories'
]

insert_query = """
    INSERT INTO fitbit_daily_activity (
        id, activity_date, total_steps, total_distance,
        tracker_distance, logged_activities_distance,
        very_active_distance, moderately_active_distance,
        light_active_distance, sedentary_active_distance,
        very_active_minutes, fairly_active_minutes,
        lightly_active_minutes, sedentary_minutes, calories
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (id, activity_date) DO NOTHING;
"""

for _, row in df[columns].iterrows():
    cur.execute(insert_query, tuple(row.values))

conn.commit()
cur.close()
conn.close()

print(f"✅ Successfully inserted {len(df)} rows into 'fitbit_daily_activity' table.")

