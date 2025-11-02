import os
import base64
import datetime as dt
import requests
import psycopg2.extras
from dotenv import load_dotenv
from db import upsert_daily_steps, upsert_daily_resting_hr, store_raw

"""
ETL complète : authentification OAuth2 → appel API Fitbit → transformation → écriture en base.
"""

load_dotenv()

print("🔍 ACCESS_TOKEN =", os.getenv("FITBIT_ACCESS_TOKEN"))
print("🔍 REFRESH_TOKEN =", os.getenv("FITBIT_REFRESH_TOKEN"))
print("🔍 USER_ID =", os.getenv("FITBIT_USER_ID"))
print("CLIENT_ID=", os.getenv("FITBIT_CLIENT_ID"))
print("CLIENT_SECRET=", os.getenv("FITBIT_CLIENT_SECRET"))
print("REDIRECT_URI =", os.getenv("FITBIT_REDIRECT_URI"))





CLIENT_ID     = os.getenv("FITBIT_CLIENT_ID")
CLIENT_SECRET = os.getenv("FITBIT_CLIENT_SECRET")
TOKEN_URL     = os.getenv("FITBIT_TOKEN_URL", "https://api.fitbit.com/oauth2/token")
REDIRECT_URI  = os.getenv("FITBIT_REDIRECT_URI")
SCOPE         = os.getenv("FITBIT_SCOPE", "activity heartrate profile")

ACCESS_TOKEN  = os.getenv("FITBIT_ACCESS_TOKEN")
REFRESH_TOKEN = os.getenv("FITBIT_REFRESH_TOKEN")
USER_ID       = os.getenv("FITBIT_USER_ID", "-")


print("🔍 CLIENT_ID:", CLIENT_ID)
print("🔍 CLIENT_SECRET:", CLIENT_SECRET[:5], "...")
print("🔍 REFRESH_TOKEN:", REFRESH_TOKEN[:8], "...")
print("🔍 REDIRECT_URI:", REDIRECT_URI)



def basic_auth_header(client_id: str, client_secret: str) -> dict:
    creds = f"{client_id}:{client_secret}"
    encoded = base64.b64encode(creds.encode()).decode()
    return {"Authorization": f"Basic {encoded}", "Content-Type": "application/x-www-form-urlencoded"}


def refresh_access_token() -> tuple[str | None, str | None]:
    global REFRESH_TOKEN
    if not REFRESH_TOKEN:
        print("⚠️ Pas de REFRESH_TOKEN configuré — fais d'abord l'OAuth via Flask.")
        return None, None

    data = {
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
    }
    headers = basic_auth_header(CLIENT_ID, CLIENT_SECRET)
    r = requests.post(TOKEN_URL, headers=headers, data=data, timeout=20)

    print("🔄 Fitbit response status:", r.status_code)
    print("🔄 Fitbit response body:", r.text[:400])

    if r.status_code != 200:
        print("❌ Refresh KO:", r.status_code, r.text[:200])
        return None, None

    js = r.json()
    return js.get("access_token"), js.get("refresh_token")



def fitbit_get(url: str, access_token: str):
    return requests.get(url, headers={"Authorization": f"Bearer {access_token}"}, timeout=20)


def ensure_token() -> str | None:
    """Retourne un token valide, sinon en génère un nouveau."""
    global ACCESS_TOKEN, REFRESH_TOKEN

    # Essaye le token actuel
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
    """ETL principal pour une date donnée."""
    global ACCESS_TOKEN, REFRESH_TOKEN

    token = ensure_token()
    if not token:
        raise RuntimeError("Aucun access_token valide. Configure l'OAuth avant l'ETL.")

    # --- Étape 1 : Steps ---
    steps_url = f"https://api.fitbit.com/1/user/{USER_ID}/activities/date/{date_str}.json"
    rs = fitbit_get(steps_url, token)
    if rs.status_code == 401:
        ACCESS_TOKEN, _ = refresh_access_token()
        rs = fitbit_get(steps_url, ACCESS_TOKEN)

    if rs.status_code != 200:
        raise RuntimeError(f"Erreur steps {rs.status_code}: {rs.text[:200]}")
    steps_json = rs.json()

    total_steps = int(steps_json.get("summary", {}).get("steps", 0))
    upsert_daily_steps(USER_ID, date_str, total_steps)
    store_raw(USER_ID, "activities/day", date_str, steps_json)

    # --- Étape 2 : Resting HR ---
    hr_url = f"https://api.fitbit.com/1/user/{USER_ID}/activities/heart/date/{date_str}.json"
    rr = fitbit_get(hr_url, ACCESS_TOKEN)
    if rr.status_code == 401:
        ACCESS_TOKEN, _ = refresh_access_token()
        rr = fitbit_get(hr_url, ACCESS_TOKEN)

    if rr.status_code != 200:
        print(f"⚠️ Warn HR {rr.status_code}: {rr.text[:200]} (je continue)")
        resting = None
    else:
        hr_json = rr.json()
        try:
            day = hr_json.get("activities-heart", [])[0]
            resting = day.get("value", {}).get("restingHeartRate")
        except Exception:
            resting = None
        store_raw(USER_ID, "heart/day", date_str, hr_json)

    upsert_daily_resting_hr(USER_ID, date_str, resting)
    print(f"✅ [OK] {date_str} steps={total_steps} resting_hr={resting}")


if __name__ == "__main__":
    date = dt.date.today().strftime("%Y-%m-%d")
    etl_for_date(date)
