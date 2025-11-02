from flask import Flask, render_template, request
from dotenv import load_dotenv
import os
import pandas as pd
import psycopg2
import plotly
from psycopg2.extras import RealDictCursor
import plotly.express as px
import json

load_dotenv()
app = Flask(__name__)

###################################################################
#######  Fonction utilitaire : chargement des données PostgreSQL
###################################################################
def load_activity_data(start_date=None, end_date=None, user_id=None):
    """
    Charge les données fitbit_dailyActivity depuis PostgreSQL avec filtres optionnels.
    """
    conn = psycopg2.connect(
        host=os.getenv("PG_HOST", "localhost"),
        dbname=os.getenv("PG_DB", "fitbitdb"),
        user=os.getenv("PG_USER", "postgres"),
        password=os.getenv("PG_PASSWORD", "password"),
        port=os.getenv("PG_PORT", 5432)
    )

    # ✅ Définir des dates par défaut réalistes (données Kaggle)
    default_start = "2016-04-01"
    default_end   = "2016-06-01"

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

#    if start_date:
#        query += " AND activity_date >= %s"
#        params.append(start_date)
#    if end_date:
#        query += " AND activity_date <= %s"
#        params.append(end_date)

    query += " ORDER BY id, activity_date"

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, params)
        rows = cur.fetchall()

    conn.close()

    df = pd.DataFrame(rows)
    if not df.empty:
        df["activity_date"] = pd.to_datetime(df["activity_date"])
    return df

#df = load_activity_data("2016-04-01", "2016-06-01", 1503960366)
#print("✅ Nombre de lignes chargées :", len(df))
#print(df.head())


#####################################################################
# ROUTE PRINCIPALE : Dashboard PostgreSQL / Kaggle
#####################################################################
@app.route("/", methods=["GET", "POST"])
def dashboard():
    start_date = request.form.get("start_date")
    end_date = request.form.get("end_date")
    user_id = request.form.get("user_id")

    df = load_activity_data(start_date, end_date, user_id)

    if df.empty:
        return render_template("dashboard2.html", tables=[], graphs=None,
                               message="⚠️ Aucune donnée trouvée pour ces critères.")

    ############################################################
    #### Graphique 1 : Évolution du nombre de pas
    ############################################################
    fig_steps = px.line(
        df, x="activity_date", y="total_steps",
        title="Évolution du nombre de pas au fil du temps",
        markers=True
    )
    fig_steps.update_layout(xaxis_title="Date", yaxis_title="Nombre de pas")
    graphJSON1 = json.dumps(fig_steps, cls=plotly.utils.PlotlyJSONEncoder)

    #########################################################
    ########  Graphique 2 : Relation Distance - Calories
    #########################################################
    fig_cal = px.scatter(
        df, x="total_distance", y="calories", size="total_steps", color="id",
        title="Relation Distance - Calories (taille = nombre de pas)",
        labels={"total_distance": "Distance totale (km)", "calories": "Calories brûlées"}
    )
    graphJSON2 = json.dumps(fig_cal, cls=plotly.utils.PlotlyJSONEncoder)

    ##########################################################
    ######## Graphique 3 : Minutes actives empilées
    #########################################################
    fig_minutes = px.bar(
        df,
        x="activity_date",
        y=["very_active_minutes", "fairly_active_minutes", "lightly_active_minutes", "sedentary_minutes"],
        title="Répartition des minutes actives par type d’activité",
        labels={"value": "Minutes", "activity_date": "Date", "variable": "Type d'activité"},
    )
    fig_minutes.update_layout(barmode="stack", xaxis_title="Date", yaxis_title="Minutes")
    graphJSON3 = json.dumps(fig_minutes, cls=plotly.utils.PlotlyJSONEncoder)

    #########################################################
    ######## Tableau de données
    #########################################################
    df_sorted = df.sort_values("activity_date", ascending=False)
    df = load_activity_data(start_date, end_date, user_id)


    table_html = df_sorted.head(10).to_html(classes="table table-striped", index=False)

    #print("🧩 Graphique 1 JSON preview:", graphJSON1[:200])  

#########################################################
    ##########   Rendu du template
#########################################################
    return render_template(
        "dashboard2.html",
        tables=[table_html],
        graphs=[graphJSON1, graphJSON2, graphJSON3],
        message=None
    )


#########################################################
    ############ Lancement du serveur Flask (sur port 5001)
#########################################################
if __name__ == "__main__":
    app.run(debug=True, port=5001)
