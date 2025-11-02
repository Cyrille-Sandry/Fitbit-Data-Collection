from dotenv import load_dotenv
import os

# Charger le .env
load_dotenv()

# Vérification
print("✅ .env loaded successfully!")
print("PG_DB:", os.getenv("PG_DB"))
print("PG_USER:", os.getenv("PG_USER"))
print("PG_PASSWORD:", os.getenv("PG_PASSWORD"))
