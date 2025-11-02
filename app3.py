from flask import Flask, render_template
import psycopg2
import pandas as pd
import plotly
import plotly.express as px
import json
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

def load_data():
    conn = psycopg2.connect(
        host=os.getenv("PG_HOST"),
        dbname=os.getenv("PG_DB"),
        user=os.getenv("PG_USER"),
        password=os.getenv("PG_PASSWORD")
    )
    #df = pd.read_sql("SELECT * FROM dummy_users", conn)
    # Sélection explicite et typage forcé
    query = """
    SELECT 
        CAST(id AS INT) AS id,
        first_name,
        last_name,
        CAST(age AS FLOAT) AS age,
        gender,
        email,
        CAST(height AS FLOAT) AS height,
        CAST(weight AS FLOAT) AS weight,
        CAST(salary AS FLOAT) AS salary,
        blood_group,
        city,
        university,
        company_name,
        department,
        title
    FROM dummy_users;
    """

    df = pd.read_sql(query, conn)

    conn.close()

    # Nettoyage basique

    df = df.dropna(subset=["age", "height", "weight", "salary"])
    df = df[(df["age"] > 0) & (df["height"] > 0) & (df["weight"] > 0)]

    return df

@app.route("/")
def dashboard():
    df = load_data()

    if df.empty:
        return "<h2>⚠️ Aucune donnée trouvée. Lance `python etl_dummyjson.py` avant de visualiser.</h2>"

    # ✅ Conversion des colonnes numériques
    #numeric_cols = ["age", "height", "weight", "salary"]
    #for col in numeric_cols:
    #    df[col] = pd.to_numeric(df[col], errors="coerce")

    # Nettoyage
    #df = df.dropna(subset=numeric_cols)
    #df = df[df["age"] > 0]

    #print(df.head(30))

    ##################################################
    # Histogramme : Distribution des âges
    ##################################################
    fig_age = px.histogram(
        df, x="age", nbins=15, color="gender",
        title="Distribution des âges",
        labels={"age": "Âge", "count": "Nombre d’individus"}
    )
    graph1 = json.dumps(fig_age, cls=plotly.utils.PlotlyJSONEncoder)

    ##################################################
    # Boxplot : Poids et Taille par genre
    ##################################################
    melted = df.melt(id_vars=["gender"], value_vars=["weight", "height"],
                     var_name="Mesure", value_name="Valeur")
    fig_box = px.box(
        melted,
        x="gender",
        y="Valeur",
        color="Mesure",
        title="Répartition du poids et de la taille selon le genre",
        points="all"
    )
    graph2 = json.dumps(fig_box, cls=plotly.utils.PlotlyJSONEncoder)

    ##################################################
    # Nuage de points : Taille vs Poids
    ##################################################
    fig_corr = px.scatter(
        df, x="height", y="weight", color="age",
        size="salary", hover_name="first_name",
        title="Corrélation Taille / Poids colorée par âge"
    )
    graph3 = json.dumps(fig_corr, cls=plotly.utils.PlotlyJSONEncoder)

    ##################################################
    # Bar chart : Salaire moyen par département
    ##################################################
    salary_df = df.groupby("department", as_index=False)["salary"].mean().dropna()
    fig_salary = px.bar(
        salary_df,
        x="department",
        y="salary",
        title="Salaire moyen par département",
        labels={"salary": "Salaire moyen ($)", "department": "Département"},
        color="salary"
    )
    graph4 = json.dumps(fig_salary, cls=plotly.utils.PlotlyJSONEncoder)

    ##################################################
    # Heatmap : Densité âge vs poids
    ##################################################
    fig_heat = px.density_heatmap(
        df, x="age", y="weight", nbinsx=20, nbinsy=20,
        color_continuous_scale="Viridis",
        title="Densité des individus (Âge vs Poids)"
    )
    graph5 = json.dumps(fig_heat, cls=plotly.utils.PlotlyJSONEncoder)

    ##################################################
    # 6️⃣ Régression : Salaire en fonction de l'âge
    ##################################################
    try:
        fig_reg = px.scatter(
            df, x="age", y="salary", color="gender",
            trendline="ols",
            title="Tendance du salaire en fonction de l’âge"
        )
    except Exception as e:
        print("⚠️ Erreur sur la régression :", e)
        fig_reg = px.scatter(title="Graphique indisponible (régression)")
    graph6 = json.dumps(fig_reg, cls=plotly.utils.PlotlyJSONEncoder)

    ##################################################
    # Table HTML (5 premières lignes)
    ##################################################
    table_html = df.head(5).to_html(classes="table table-striped", index=False)

    return render_template(
        "dashboard3.html",
        graphs=[graph1, graph2, graph3, graph4, graph5, graph6],
        table=table_html
    )

if __name__ == "__main__":
    app.run(debug=True, port=5003)
