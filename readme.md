# 🩺 Fitbit End-to-End Data Pipeline  
### Flask + OAuth 2.0 + Python ETL + PostgreSQL + Chart.js

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-black?logo=flask)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue?logo=postgresql)
![OAuth2](https://img.shields.io/badge/Auth-OAuth%202.0-green)
![Fitbit](https://img.shields.io/badge/API-Fitbit-purple?logo=fitbit)

---

## 📚 Table des matières

1. [🎯 Description du projet](#-description-du-projet)  
2. [🎓 Objectifs pédagogiques](#-objectifs-pédagogiques)  
3. [⚙️ Architecture du pipeline](#️-architecture-du-pipeline)  
4. [🧰 Technologies utilisées](#-technologies-utilisées)  
5. [📂 Structure du projet](#-structure-du-projet)  
6. [🔧 Installation & Configuration](#-installation--configuration)  
7. [🚀 Exécution](#-exécution)  
8. [🧠 Fonctionnement du pipeline](#-fonctionnement-du-pipeline)  
9. [📊 Visualisation et Dashboard](#-visualisation-et-dashboard)  
10. [🧩 Base de données PostgreSQL](#-base-de-données-postgresql)  
11. [🔐 Authentification OAuth 20](#-authentification-oauth-20)  
12. [🧰 Dépannage](#-dépannage)  
13. [🚀 Extensions possibles](#-extensions-possibles)  
14. [📜 Auteur](#-auteur)

---

## 🎯 Description du projet

Ce projet illustre la création d’un **pipeline de données complet (ETL)** appliqué à des données **Fitbit**.  
L’objectif est de construire une solution de **bout en bout** :

> De la collecte automatique des données via l’API Fitbit  
> 👉 à leur transformation, stockage et visualisation dans une application web Flask.

Le pipeline :
- Authentifie l’utilisateur via **OAuth 2.0**
- Extrait des données Fitbit (pas, rythme cardiaque)
- Les transforme et les charge dans une **base PostgreSQL**
- Les visualise dans un **dashboard interactif Chart.js**

---

## 🎓 Objectifs pédagogiques

- Comprendre le fonctionnement d’une **API REST sécurisée par OAuth 2.0**
- Mettre en place un **pipeline ETL** complet (Extract → Transform → Load)
- Manipuler des **données JSON** issues d’API
- Gérer une base **relationnelle PostgreSQL**
- Construire une **interface Flask + Chart.js**
- Exposer une application locale avec **ngrok**

---

## ⚙️ Architecture du pipeline

```text
[Fitbit API]
     │   (OAuth 2.0)
     ▼
[Python - requests / Flask]
     │   (Transformation)
     ▼
[PostgreSQL]
     │   (Stockage structuré + JSON brut)
     ▼
[Chart.js Dashboard]
```

---

## 🧰 Technologies utilisées

| Composant | Technologie / Lib | Rôle |
|------------|------------------|------|
| **API Source** | Fitbit Web API | Données d’activité, sommeil, fréquence cardiaque |
| **Langage** | Python 3.10+ | Langage principal du pipeline |
| **Framework Web** | Flask | Authentification + visualisation |
| **Base de données** | PostgreSQL | Stockage structuré des données |
| **Tunnel HTTPS** | ngrok | Accès externe à Flask pour l’OAuth |
| **Librairies** | `requests`, `psycopg2-binary`, `python-dotenv` | Connexion API, DB et config |
| **Visualisation** | Chart.js | Graphiques du dashboard |
| **Outil test** | Postman | Test des endpoints API Fitbit |

---

## 📂 Structure du projet

```bash
fitbit-pipeline/
│
├── app.py                 # Application Flask (OAuth + Dashboard)
├── etl_fitbit.py          # Script ETL (extraction, transformation, chargement)
├── db.py                  # Fonctions utilitaires pour PostgreSQL
├── schema.sql             # Schéma de la base de données
├── requirements.txt       # Dépendances Python
├── .env.example           # Exemple de variables d'environnement
│
├── templates/
│   ├── index.html         # Page d'accueil
│   ├── dashboard.html     # Visualisation (Chart.js)
│   └── error.html         # Gestion des erreurs
│
└── README.md
```

---

## 🔧 Installation & Configuration

### 1️⃣ Cloner le dépôt
```bash
git clone https://github.com/<votre_repo>/fitbit-pipeline.git
cd fitbit-pipeline
```

### 2️⃣ Créer un environnement virtuel
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# ou
venv\Scripts\activate     # Windows
```

### 3️⃣ Installer les dépendances
```bash
pip install -r requirements.txt
```

### 4️⃣ Configurer la base PostgreSQL
```bash
createdb fitbitdb
psql -d fitbitdb -f schema.sql
```

### 5️⃣ Configurer Fitbit Developer
1. Crée ton app sur [https://dev.fitbit.com/apps](https://dev.fitbit.com/apps)
2. Type : **Server**  
   Callback URL : `https://oauth.pstmn.io/v1/callback` (puis remplacé par ngrok)
3. Scopes : `activity heartrate profile`
4. Note ton **Client ID** et **Client Secret**

### 6️⃣ Configurer ngrok
```bash
ngrok http 5000
```
Copie l’URL HTTPS (ex : `https://xxxx.ngrok.dev`)  
➡️ Mets-la dans Fitbit : `Redirect URL = https://xxxx.ngrok.dev/callback`

### 7️⃣ Configurer les variables d’environnement
```bash
cp .env
```
Puis remplis :
```env
FITBIT_CLIENT_ID=ton_client_id
FITBIT_CLIENT_SECRET=ton_secret
FITBIT_REDIRECT_URI=https://xxxx.ngrok.dev/callback
FITBIT_SCOPE=activity heartrate profile

PG_USER=postgres
PG_PASSWORD=postgres
PG_DB=fitbitdb
```

---

## 🚀 Exécution

### Lancer l’application Flask
```bash
python app.py
```

Visite l’URL affichée par **ngrok**, par ex :
```
https://xxxx.ngrok.dev
```

### Lancer le pipeline ETL
```bash
python etl_fitbit.py
```

Par défaut, il récupère les données du jour.

---

## 🧠 Fonctionnement du pipeline

### 1️⃣ **Extraction**
- Appel de l’API Fitbit via `requests.get()`
- Endpoints utilisés :
  - `/1/user/-/activities/date/YYYY-MM-DD.json` → pas quotidiens  
  - `/1/user/-/activities/heart/date/YYYY-MM-DD.json` → rythme cardiaque

### 2️⃣ **Transformation**
- Conversion du JSON en valeurs claires (steps, resting_hr)
- Nettoyage des données manquantes
- Formatage de la date

### 3️⃣ **Chargement**
- Insertion dans PostgreSQL via `psycopg2`
- Trois tables :
  - `daily_steps`
  - `daily_resting_hr`
  - `raw_fitbit_responses` (JSON brut)

### 4️⃣ **Visualisation**
- Flask rend la page `/dashboard`
- Graphiques Chart.js : distances et nombre de pas

---

## 📊 Visualisation et Dashboard

**Page `/dashboard` :**
- Sélecteur de date  
- Nombre total de pas  
- Graphique des distances (Chart.js)  
- Bloc affichant le JSON brut Fitbit

---

## 🧩 Base de données PostgreSQL

### Table `daily_steps`
| Colonne | Type | Description |
|----------|------|-------------|
| user_id | TEXT | ID utilisateur Fitbit |
| date | DATE | Jour concerné |
| steps | INTEGER | Nombre total de pas |
| created_at | TIMESTAMP | Date d’insertion |

### Table `daily_resting_hr`
| Colonne | Type | Description |
|----------|------|-------------|
| user_id | TEXT | ID utilisateur Fitbit |
| date | DATE | Jour concerné |
| resting_hr | INTEGER | Rythme cardiaque au repos |

### Table `raw_fitbit_responses`
| Colonne | Type | Description |
|----------|------|-------------|
| user_id | TEXT | ID utilisateur Fitbit |
| endpoint | TEXT | Endpoint appelé |
| date | DATE | Date |
| payload | JSONB | Réponse JSON complète |

---

## 🔐 Authentification OAuth 2.0

1. L’utilisateur clique sur **“Se connecter à Fitbit”**
2. Fitbit redirige vers `/callback` avec un `code`
3. Flask échange le `code` contre :
   - `access_token`
   - `refresh_token`
   - `user_id`
4. Ces informations sont utilisées pour appeler l’API Fitbit.

---

## 🧰 Dépannage

| Erreur | Cause probable | Solution |
|--------|----------------|-----------|
| `invalid_grant` | Mauvaise Redirect URI | Vérifie qu’elle correspond EXACTEMENT |
| `invalid_request` | Paramètre manquant (grant_type/code) | Vérifie ta requête OAuth |
| `401 Unauthorized` | Token expiré | Rafraîchir avec le refresh_token |
| `SSL required` | URL non HTTPS | Utilise ngrok |
| `KeyError` | JSON vide / clé manquante | Vérifie la structure du JSON Fitbit |

---

## Auteur

Projet réalisé dans le cadre du module  
**“End-to-End Data Pipeline”**

- 👨‍💻 Développeur : *[Cyrille Simeu]*  
- 🗓️ Année académique : 2025





