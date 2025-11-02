import os, base64, datetime as dt
from urllib.parse import urlencode
import requests
from flask import Flask, render_template, request, redirect, session, url_for
from dotenv import load_dotenv
from db import upsert_daily_steps, upsert_daily_resting_hr, store_raw
from etl_fitbit import etl_for_date  # on réutilise la logique ETL
import psycopg2.extras

"""
Ce script Flask fait un flow OAuth Fitbit + un mini-dashboard qui déclenche l'ETL pour une date donnée, 
puis affiche des métriques.
"""


# Permet de charger .env dans l'environnement du processus
load_dotenv()

# Clé de la session pour la production
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret")



# Paramètres de connexion
CLIENT_ID     = os.getenv("FITBIT_CLIENT_ID")
CLIENT_SECRET = os.getenv("FITBIT_CLIENT_SECRET")
AUTH_URL      = os.getenv("FITBIT_AUTH_URL", "https://www.fitbit.com/oauth2/authorize")
TOKEN_URL     = os.getenv("FITBIT_TOKEN_URL", "https://api.fitbit.com/oauth2/token")
REDIRECT_URI  = os.getenv("FITBIT_REDIRECT_URI")
SCOPE         = os.getenv("FITBIT_SCOPE", "activity heartrate profile")



# Fonction pour la construction de headers
def basic_auth_header(cid, csec):
    """
    Construit l'en-tête 'Authorization: Basic <base64(client_id:client_secret)>'
    exigé par l'endpoint token OAuth2 de Fitbit (RFC 6749).
    """
    creds = f"{cid}:{csec}"
    enc = base64.b64encode(creds.encode()).decode()
    return {"Authorization": f"Basic {enc}", "Content-Type": "application/x-www-form-urlencoded"}

# Fonction qui permet d'indiquer si l'utilisateur est connecté.
def is_auth():
    return "access_token" in session and "user_id" in session



@app.route("/")
def index():
    # Passe un flag au template pour afficher un bouton login/logout adapté
    return render_template("index.html", is_auth=is_auth())

@app.route("/login")
def login():
    """
    Démarre le flow OAuth2 Authorization Code :
      - Construit l'URL d'autorisation
      - Redirige l'utilisateur vers Fitbit pour consentement.
    """
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPE
    }
    return redirect(f"{AUTH_URL}?{urlencode(params)}")

@app.route("/callback")
def callback():
    """
    Endpoint de redirection après consentement :
      - Reçoit 'code' (ou 'error')
      - Échange 'code' contre access_token/refresh_token
      - Stocke les tokens en session (démo)
      - Redirige vers /dashboard
    """
    if "error" in request.args:
        return render_template("error.html", message=request.args["error"]), 400
    code = request.args.get("code")
    if not code:
        return render_template("error.html", message="Code manquant"), 400
    
    # POST token (authorization_code grant)
    data = {
        "client_id": CLIENT_ID,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
        "code": code
    }

    # Echange code contre des jetons
    r = requests.post(TOKEN_URL, 
                      headers=basic_auth_header(CLIENT_ID, CLIENT_SECRET), 
                      data=data, 
                      timeout=20)
    if r.status_code != 200:
        return render_template("error.html", message=f"Token KO {r.status_code}: {r.text[:200]}"), 400
    js = r.json()

    # stocke en session (démo)
    session["access_token"]  = js.get("access_token")
    session["refresh_token"] = js.get("refresh_token")
    session["user_id"]       = js.get("user_id")
    session["scope"]         = js.get("scope")
    return redirect(url_for("dashboard"))

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    """
    Page principale :
      - Choisir la date (POST 'date' ou aujourd’hui par défaut)
      - Lancer l’ETL pour cette date (écrit en DB + stocke RAW)
      - Appeler Fitbit pour récupérer les steps (pour affichage immédiat)
      - Rendre 'dashboard.html' avec steps + distances (labels/values)
    """

    if not is_auth():
        return redirect(url_for("index"))

    #  Récupère la date soumise (POST) ou prend la date du jour (YYYY-MM-DD)
    date_str = request.form.get("date") if request.method == "POST" else dt.date.today().strftime("%Y-%m-%d")

    # Lance l’ETL pour la date (récupère depuis Fitbit et charge la DB)
    try:
        # Pour l’ETL, expose via variables d’env (simple) : ACCESS/REFRESH/USER
        os.environ["FITBIT_ACCESS_TOKEN"]  = session.get("access_token", "") or ""
        os.environ["FITBIT_REFRESH_TOKEN"] = session.get("refresh_token", "") or ""
        os.environ["FITBIT_USER_ID"]       = session.get("user_id", "-") or "-"

        etl_for_date(date_str)
    except Exception as e:
        # En cas d'erreur ETL (ex: token invalide, DB down...), on affiche une page d’erreur
        return render_template("error.html", message=f"ETL KO: {e}")

    # Appelle l’API Fitbit directement pour afficher sur la page (optionnel)
    # Ici, on affiche au moins les steps via l’appel “activities/date”
    steps_url = f"https://api.fitbit.com/1/user/-/activities/date/{date_str}.json"
    rs = requests.get(steps_url, headers={"Authorization": f"Bearer {session['access_token']}"} , timeout=20)

    if rs.status_code != 200:
        return render_template("error.html", 
                               message=f"API KO {rs.status_code}: {rs.text[:200]}")
    
    # Prépare les données pour le template (ex: chart "distances" par type d’activité)
    data = rs.json()
    steps = int(data.get("summary", {}).get("steps", 0))
    distances = data.get("summary", {}).get("distances", [])
    labels = [d.get("activity", "unknown") for d in distances]
    values = [d.get("distance", 0) for d in distances]

    return render_template("dashboard.html",
                           date_str=date_str,
                           steps=steps,
                           json_raw=data,
                           labels=labels,
                           values=values)

@app.route("/logout")
def logout():
    """Déconnecte l’utilisateur : vide la session et renvoie à l’accueil."""
    session.clear()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
