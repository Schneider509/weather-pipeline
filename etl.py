import os
import time
import requests
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

# Liste des 50 villes
CITIES_LIST = [
    "Paris", "Marseille", "Lyon", "Toulouse", "Nice", "Nantes", "Montpellier",
    "Strasbourg", "Bordeaux", "Lille", "Rennes", "Toulon", "Reims", "Saint-Étienne",
    "Le Havre", "Dijon", "Angers", "Grenoble", "Nîmes", "Aix-en-Provence",
    "Brest", "Le Mans", "Amiens", "Tours", "Limoges", "Clermont-Ferrand", "Villeurbanne",
    "Besançon", "Orléans", "Metz", "Rouen", "Mulhouse", "Perpignan", "Caen", "Boulogne-Billancourt",
    "Nancy", "Argenteuil", "Saint-Denis", "Roubaix", "Tourcoing", "Montreuil", "Avignon",
    "Nanterre", "Poitiers", "Créteil", "Versailles", "Pau", "Courbevoie", "Vitry-sur-Seine", "Calais"
]

def get_coordinates(city_name):
    """Récupère automatiquement la latitude et longitude."""
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": city_name, "count": 1, "language": "fr", "format": "json"}
    try:
        res = requests.get(url, params=params, timeout=5)
        data = res.json()
        if "results" in data and len(data["results"]) > 0:
            result = data["results"][0]
            return {"city": city_name, "lat": result["latitude"], "lon": result["longitude"]}
    except Exception as e:
        print(f"Erreur géocodage pour {city_name} : {e}")
    return None

def extract_city_weather(city_info):
    """Extrait l'historique horaire des 30 derniers jours consolidés."""
    today = datetime.utcnow().date()
    end_date = today - timedelta(days=2)       # Décalage de 48h pour les archives consolidées
    start_date = end_date - timedelta(days=30)

    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": city_info["lat"],
        "longitude": city_info["lon"],
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "hourly": ["temperature_2m", "relative_humidity_2m", "wind_speed_10m"],
        "timezone": "auto"
    }
    response = requests.get(url, params=params, timeout=10)
    if response.status_code == 200:
        return response.json()
    return None

def transform_city_weather(raw_data, city_name):
    if not raw_data or "hourly" not in raw_data:
        return None
    
    hourly = raw_data["hourly"]
    df = pd.DataFrame({
        "city": city_name,
        "latitude": raw_data.get("latitude"),
        "longitude": raw_data.get("longitude"),
        "timestamp": hourly.get("time"),
        "temperature_cels": hourly.get("temperature_2m"),
        "humidity_percent": hourly.get("relative_humidity_2m"),
        "wind_speed_kmh": hourly.get("wind_speed_10m")
    })
    
    df["extracted_at"] = datetime.utcnow()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["extracted_at"] = pd.to_datetime(df["extracted_at"])
    return df

def load_data(df):
    if df is None or df.empty:
        print("Aucune donnée à insérer.")
        return

    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")

    engine = create_engine(f"postgresql://{user}:{password}@{host}:{port}/{db_name}")

    df.to_sql("staging_cities_weather", con=engine, if_exists="replace", index=False)

    upsert_query = text("""
        INSERT INTO cities_weather (
            city, latitude, longitude, timestamp, 
            temperature_celsius, humidity_percent, wind_speed_kmh, extracted_at
        )
        SELECT 
            city, latitude, longitude, timestamp, 
            temperature_celsius, humidity_percent, wind_speed_kmh, extracted_at
        FROM staging_cities_weather
        ON CONFLICT (city, timestamp) 
        DO UPDATE SET
            temperature_celsius = EXCLUDED.temperature_celsius,
            humidity_percent = EXCLUDED.humidity_percent,
            wind_speed_kmh = EXCLUDED.wind_speed_kmh,
            extracted_at = EXCLUDED.extracted_at;

        DROP TABLE staging_cities_weather;
    """)

    with engine.begin() as conn:
        conn.execute(upsert_query)

    print(f"-> Ingestion réussie : {len(df)} lignes synchronisées dans PostgreSQL.")

if __name__ == "__main__":
    print(f"--- Démarrage du pipeline : {len(CITIES_LIST)} villes ---")
    
    frames = []
    # On parcourt bien l'ensemble des villes
    for city_name in set(CITIES_LIST):
        coords = get_coordinates(city_name)
        if coords:
            print(f"Extraction historique pour {city_name}...")
            raw = extract_city_weather(coords)
            df_city = transform_city_weather(raw, city_name)
            if df_city is not None:
                frames.append(df_city)
        time.sleep(0.15)  # Pause légère pour respecter les quotas de requêtes
            
    if frames:
        final_df = pd.concat(frames, ignore_index=True)
        print(f"Total de lignes prêtes : {len(final_df)}")
        load_data(final_df)
        
    print("--- Pipeline terminé ---")