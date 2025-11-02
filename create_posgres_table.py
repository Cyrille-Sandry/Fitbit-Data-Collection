import psycopg2
import os
from psycopg2 import sql
from dotenv import load_dotenv

# Charger les variables d'environnement (.env)
load_dotenv()

# Paramètres de connexion PostgreSQL
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5432")
PG_DB = os.getenv("PG_DB", "fitbitdb")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "postgres")

# Script SQL de création des tables (reprend le contenu de schema.sql)
CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS daily_steps (
    user_id TEXT NOT NULL,
    date DATE NOT NULL,
    steps INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, date)
);

CREATE TABLE IF NOT EXISTS daily_resting_hr (
    user_id TEXT NOT NULL,
    date DATE NOT NULL,
    resting_hr INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, date)
);

CREATE TABLE IF NOT EXISTS raw_fitbit_responses (
    user_id TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    date DATE NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, endpoint, date)
);
"""

def create_tables():
    """Crée les tables nécessaires dans la base PostgreSQL."""
    try:
        # Connexion à la base
        print(f"Connexion à PostgreSQL ({PG_DB})...")
        conn = psycopg2.connect(
            host=PG_HOST,
            port=PG_PORT,
            dbname=PG_DB,
            user=PG_USER,
            password=PG_PASSWORD
        )
        conn.autocommit = True  # exécuter sans transaction explicite

        # Exécution du SQL
        with conn.cursor() as cur:
            print("Création des tables...")
            cur.execute(CREATE_TABLES_SQL)
            print("✅ Tables créées avec succès !")

    except Exception as e:
        print("Erreur lors de la création des tables :", e)
    finally:
        if conn:
            conn.close()
            print("🔒 Connexion fermée.")

if __name__ == "__main__":
    create_tables()
