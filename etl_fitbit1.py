import os
import base64
import datetime as dt
import requests
import psycopg2.extras
from dotenv import load_dotenv
from db import upsert_daily_steps, upsert_daily_resting_hr, store_raw

"""
Ce script fait une ETL complete : authentification OAuth2 → appel API Fitbit → transformation → écriture en base (via le module db).

"""


# Permet de charger .env dans l'environnement du processus
load_dotenv()

CLIENT_ID     = os.getenv("FITBIT_CLIENT_ID")
CLIENT_SECRET = os.getenv("FITBIT_CLIENT_SECRET")
TOKEN_URL     = os.getenv("FITBIT_TOKEN_URL", "https://api.fitbit.com/oauth2/token")
REDIRECT_URI  = os.getenv("FITBIT_REDIRECT_URI")
SCOPE         = os.getenv("FITBIT_SCOPE", "activity heartrate profile")

#Ces variables supposent qu'on a  déjà fait un 1er OAuth

ACCESS_TOKEN  = os.getenv("FITBIT_ACCESS_TOKEN")   # optionnel si tu gères refresh à la volée
REFRESH_TOKEN = os.getenv("FITBIT_REFRESH_TOKEN")  # nécessaire pour régénérer ACCESS_TOKEN
USER_ID       = os.getenv("FITBIT_USER_ID", "-")   # '-' = current user


# Fonction pour la construction de l'entête Fitbit

def basic_auth_header(client_id: str, client_secret: str) -> dict:
    """
    Construit l'en-tête HTTP 'Authorization: Basic ...' exigé par Fitbit
    pour l'échange de token (RFC 6749). Format: base64("client_id:client_secret").
    """
    creds = f"{client_id}:{client_secret}"
    encoded = base64.b64encode(creds.encode()).decode()
    return {"Authorization": f"Basic {encoded}", "Content-Type": "application/x-www-form-urlencoded"}





def refresh_access_token() -> tuple[str | None, str | None]:
    """
    Utilise le refresh_token pour obtenir un nouveau access_token (et parfois un nouveau refresh_token).
    Retourne (access_token, refresh_token) ou (None, None) si échec.
    """
    if not REFRESH_TOKEN:
        print("Pas de REFRESH_TOKEN configuré — fais d'abord l'OAuth dans Postman/Flask.")
        return None, None

    data = {
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
    }
    headers = basic_auth_header(CLIENT_ID, CLIENT_SECRET)
    r = requests.post(TOKEN_URL, headers=headers, data=data, timeout=20)
    if r.status_code != 200:
        print("Refresh KO:", r.status_code, r.text[:200])
        return None, None
    js = r.json()
    return js.get("access_token"), js.get("refresh_token")




def fitbit_get(url: str, access_token: str):
    """
    GET générique vers l'API Fitbit avec Bearer token.
    On renvoie l'objet Response pour laisser l'appelant gérer le statut/JSON.
    """
    r = requests.get(url, headers={"Authorization": f"Bearer {access_token}"}, timeout=20)
    return r



def ensure_token() -> str | None:
    """
    Garantit un access_token valide.
    - Si on a déjà ACCESS_TOKEN en mémoire, on le réutilise.
    - Sinon, tente un refresh à partir de REFRESH_TOKEN.
    Met à jour les globals ACCESS_TOKEN / REFRESH_TOKEN si succès.
    """
    global ACCESS_TOKEN, REFRESH_TOKEN
    # Premier essai avec token courant
    if ACCESS_TOKEN:
        return ACCESS_TOKEN
    # Sinon tente un refresh
    new_access, new_refresh = refresh_access_token()
    if new_access:
        ACCESS_TOKEN = new_access
        if new_refresh:
            REFRESH_TOKEN = new_refresh
        return ACCESS_TOKEN
    return None

def etl_for_date(date_str: str):
    """
    Pipeline ETL pour une date donnée (YYYY-MM-DD):
      - Extract: appels API Fitbit (steps, resting HR)
      - Transform: extraction des métriques utiles
      - Load: upsert en DB + stockage des payloads bruts
    """
    token = ensure_token()
    if not token:
        raise RuntimeError("Aucun access_token valide. Configure l'OAuth avant l'ETL.")

    # --- Steps ---
    steps_url = f"https://api.fitbit.com/1/user/{USER_ID}/activities/date/{date_str}.json"
    rs = fitbit_get(steps_url, token)
    if rs.status_code == 401:
        # token expiré → refresh et retry
        ACCESS_TOKEN, _ = refresh_access_token()
        rs = fitbit_get(steps_url, ACCESS_TOKEN)
    if rs.status_code != 200:
        raise RuntimeError(f"Erreur steps {rs.status_code}: {rs.text[:200]}")
    steps_json = rs.json()

    # Transformation: total steps jour
    total_steps = int(steps_json.get("summary", {}).get("steps", 0))
    upsert_daily_steps(USER_ID, date_str, total_steps)
    store_raw(USER_ID, "activities/day", date_str, steps_json)

    # --- Resting HR ---
    hr_url = f"https://api.fitbit.com/1/user/{USER_ID}/activities/heart/date/{date_str}.json"
    rr = fitbit_get(hr_url, ACCESS_TOKEN)
    if rr.status_code == 401:
        ACCESS_TOKEN, _ = refresh_access_token()
        rr = fitbit_get(hr_url, ACCESS_TOKEN)
    if rr.status_code != 200:
        print(f"Warn HR {rr.status_code}: {rr.text[:200]} (je continue)")
        resting = None
    else:
        hr_json = rr.json()
        # Selon les réponses Fitbit, resting HR peut être à différents endroits:
        # Ex: "activities-heart": [{"dateTime": "YYYY-MM-DD", "value": {"restingHeartRate": 63}}]
        try:
            day = hr_json.get("activities-heart", [])[0]
            resting = day.get("value", {}).get("restingHeartRate")
        except Exception:
            resting = None

        store_raw(USER_ID, "heart/day", date_str, hr_json)

    upsert_daily_resting_hr(USER_ID, date_str, resting)
    print(f"[OK] {date_str} steps={total_steps} resting_hr={resting}")

if __name__ == "__main__":
    # Par défaut: aujourd'hui (timezone Europe/Brussels si tu veux gérer le décalage)
    date = dt.date.today().strftime("%Y-%m-%d")
    etl_for_date(date)
