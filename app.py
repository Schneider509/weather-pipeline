import os
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px
from dotenv import load_dotenv

load_dotenv()

# Configuration de la page Streamlit
st.set_page_config(
    page_title="Weather Analytics Dashboard",
    page_icon="🌤️",
    layout="wide"
)

# Connexion mise en cache à PostgreSQL
@st.cache_resource
def get_database_connection():
    user = os.getenv("DB_USER", "dev_user")
    password = os.getenv("DB_PASSWORD", "dev_password")
    host = "localhost"  # Port mappé sur l'hôte local
    port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "weather_db")
    
    url = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
    return create_engine(url)

engine = get_database_connection()

@st.cache_data(ttl=600)
def load_data():
    query = """
        SELECT 
            city, 
            latitude, 
            longitude, 
            timestamp, 
            temperature_celsius, 
            humidity_percent, 
            wind_speed_kmh,
            extracted_at
        FROM cities_weather
        ORDER BY timestamp DESC;
    """
    df = pd.read_sql(query, con=engine)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df

st.title("🌤️ French Cities Weather Intelligence")
st.markdown("Dashboard analytique alimenté en continu par Apache Airflow & PostgreSQL.")

with st.spinner("Chargement des métriques météo..."):
    df = load_data()

if df.empty:
    st.warning("Aucune donnée trouvée dans la base de données PostgreSQL.")
    st.stop()

# Barre latérale : Filtres
st.sidebar.header("🔍 Filtres")

cities_available = sorted(df["city"].unique().tolist())
selected_city = st.sidebar.selectbox(
    "Sélectionnez une ville :", 
    cities_available, 
    index=cities_available.index("Paris") if "Paris" in cities_available else 0
)

# Filtrage par ville
df_city = df[df["city"] == selected_city].sort_values("timestamp")
latest_record = df_city.iloc[-1]

# KPIs principaux
st.subheader(f"Dernières observations pour **{selected_city}** ({latest_record['timestamp'].strftime('%d/%m/%Y %H:%M')})")

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("🌡️ Température", f"{latest_record['temperature_celsius']} °C")
kpi2.metric("💧 Humidité", f"{latest_record['humidity_percent']} %")
kpi3.metric("💨 Vent", f"{latest_record['wind_speed_kmh']} km/h")
kpi4.metric("📊 Données collectées", f"{len(df_city):,} pts")

st.divider()

# Graphiques temporels
col_left, col_right = st.columns(2)

with col_left:
    st.markdown("### Évolution des Températures (30 derniers jours)")
    fig_temp = px.line(
        df_city, 
        x="timestamp", 
        y="temperature_celsius", 
        title=f"Température horaire - {selected_city}",
        labels={"timestamp": "Date & Heure", "temperature_celsius": "Température (°C)"},
        color_discrete_sequence=["#FF4B4B"]
    )
    st.plotly_chart(fig_temp, use_container_width=True)

with col_right:
    st.markdown("### Évolution du Vent & de l'Humidité")
    fig_wind = px.line(
        df_city, 
        x="timestamp", 
        y=["humidity_percent", "wind_speed_kmh"], 
        title=f"Humidité vs Vitesse du vent - {selected_city}",
        labels={"value": "Mesure", "timestamp": "Date & Heure", "variable": "Indicateur"},
        color_discrete_sequence=["#1F77B4", "#2CA02C"]
    )
    st.plotly_chart(fig_wind, use_container_width=True)

# Carte thermique nationale
st.divider()
st.subheader("🗺️ Vue d'ensemble : Températures actuelles à travers la France")

latest_per_city = df.sort_values("timestamp").groupby("city").last().reset_index()

fig_map = px.scatter_map(
    latest_per_city,
    lat="latitude",
    lon="longitude",
    hover_name="city",
    hover_data={
        "temperature_celsius": True, 
        "humidity_percent": True, 
        "wind_speed_kmh": True, 
        "latitude": False, 
        "longitude": False
    },
    color="temperature_celsius",
    size="temperature_celsius",
    color_continuous_scale="Turbo",
    size_max=15,
    zoom=4.7,
    center={"lat": 46.603354, "lon": 1.888334},
    map_style="carto-positron",
    title="Carte thermique des 50 villes"
)
st.plotly_chart(fig_map, use_container_width=True)