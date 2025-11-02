import os
import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from dotenv import load_dotenv

"""
@contextmanager est décorateur pratique pour créer des contextes managés (comme le mot-clé with), 
ce qui permet de garantir que la connexion à la base est proprement ouverte et fermée, même en cas d’erreur.
"""
# Define the connection parameters that can be found in the env 

PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = int(os.getenv("PG_PORT", "5432"))
PG_DB   = os.getenv("PG_DB", "fitbitdb")
PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD  = os.getenv("PG_PASSWORD", "CyUlb2025")

# Connection function that create and returns a postgreSQL connection.
"""
Encapsuler la création de connexion dans cette fonction permet d'éviter la répétition dans le code.

"""
def get_conn():
    return psycopg2.connect(
        host=PG_HOST, 
        port=PG_PORT, 
        dbname=PG_DB, 
        user=PG_USER, 
        password=PG_PASSWORD
    )

"""
Bloc pour la gestion des transactions:
Le bloc de code ci-dessous:
    - Crée une connection à la base de données à travers conn = get_conn()
    - Ouvre un curseur (objet pour exécuter les requettes SQL)
    - Le With garantit que le curseur sera fermé automatiquement à la fin
    - yield cur: permet de renvoyer le curseur temporairement à la fonction appelante par exemple upsert_daily_steps() tout en gardant le contrôle du flux de gestion
    - conn.commit() : Si tout se passe bien, la transaction est validée, les modifications sont enregistrées.
    - except Exceptions: si une erreur se produit, la transaction est annulée
    - conn.rollback():  pour éviter de corrompre la base.
    - finally: conn.close() la connection est fermée proprement quoi qu'il arrive.

"""

@contextmanager
def db_cursor():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            yield cur
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

"""
Fonction upsert_daily_steps():

Permet d'insérer ou mettre à jour le nombre de pas quotidiens d’un utilisateur.
   - cur.execute() exécute une requête SQL paramétrée (évite les injections SQL).
   - (%s, %s, %s) sont des paramètres placeholders remplacés par les valeurs fournies après la requête.
   - ON CONFLICT (user_id, date) signifie : Si une ligne avec le même (user_id, date) existe déjà, alors on met à jour au lieu d’insérer.
   - EXCLUDED.steps fait référence à la valeur proposée dans l’instruction INSERT.
   - created_at = NOW() met à jour la date de dernière modification.

Le UPSERT (update or insert) est  pratique pour maintenir des données journalières
"""


def upsert_daily_steps(user_id: str, date_str: str, steps: int):
    with db_cursor() as cur:
        cur.execute("""
            INSERT INTO daily_steps (user_id, date, steps)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id, date)
            DO UPDATE SET steps = EXCLUDED.steps, created_at = NOW();
        """, (user_id, date_str, steps))

"""
Fonctions upsert_daily_resting_hr() pour les fréquence cardiaques
"""

def upsert_daily_resting_hr(user_id: str, date_str: str, resting_hr: int | None):
    with db_cursor() as cur:
        cur.execute("""
            INSERT INTO daily_resting_hr (user_id, date, resting_hr)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id, date)
            DO UPDATE SET resting_hr = EXCLUDED.resting_hr, created_at = NOW();
        """, (user_id, date_str, resting_hr))


"""
Fonction store_raw()
  - Permet d'enregistrer la réponse brute de l’API Fitbit (ou toute autre source).
  - Le champ payload contient un objet JSON.
  - psycopg2.extras.Json(payload) convertit le dictionnaire Python en JSON PostgreSQL automatiquement.
  - ON CONFLICT gère les doublons (user_id, endpoint, date) comme précédemment.
"""


def store_raw(user_id: str, endpoint: str, date_str: str, payload: dict):
    with db_cursor() as cur:
        cur.execute("""
            INSERT INTO raw_fitbit_responses (user_id, endpoint, date, payload)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (user_id, endpoint, date)
            DO UPDATE SET payload = EXCLUDED.payload, created_at = NOW();
        """, (user_id, endpoint, date_str, psycopg2.extras.Json(payload)))
