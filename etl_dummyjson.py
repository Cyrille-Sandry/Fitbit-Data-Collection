import requests
from db_dummyjson import insert_user


"""
Ce script ETL simule un flux Fitbit.
Il extrait des données utilisateurs depuis DummyJSON,
génère des "steps" et "calories" factices,
puis les enregistre dans PostgreSQL.
"""


def etl_dummyjson():
    print("Lancement de l’ETL enrichi DummyJSON...")
    url = "https://dummyjson.com/users?limit=100"
    response = requests.get(url)
    users = response.json().get("users", [])

    for user in users:
        data = {
            "first_name": user.get("firstName"),
            "last_name": user.get("lastName"),
            "age": user.get("age"),
            "gender": user.get("gender"),
            "email": user.get("email"),
            "phone": user.get("phone"),
            "blood_group": user.get("bloodGroup"),
            "height": user.get("height"),
            "weight": user.get("weight"),
            "eye_color": user.get("eyeColor"),
            "university": user.get("university"),
            "city": user.get("address", {}).get("city"),
            "company_name": user.get("company", {}).get("name"),
            "department": user.get("company", {}).get("department"),
            "title": user.get("company", {}).get("title"),
            "salary": user.get("company", {}).get("address", {}).get("postalCode", 0)  # simulation
        }
        insert_user(data)

    print(f"✅ {len(users)} utilisateurs insérés dans la base PostgreSQL !")

if __name__ == "__main__":
    etl_dummyjson()
