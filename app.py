import os
import streamlit as st
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

st.set_page_config(
    page_title="Weather Analytics - 30 Derniers Jours",
    page_icon="🌤️",
    layout="wide"
)

@st.cache_data(ttl=300)
def load_data_from_db():
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")

    url = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
    engine = create_engine(url)
    
    query = """
        SELECT city, timestamp, temperature_celsius, humidity_percent, wind_speed_kmh, extracted_at
        FROM cities_weather
        ORDER BY timestamp ASC;
    """
    df = pd.read_sql(query, con=engine)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df

st.title("🌤️ Analyse Météo Historique (30 Derniers Jours)")
st.caption("Données historiques stockées dans PostgreSQL local.")

try:
    df = load_data_from_db()

    # Barre latérale : Filtres
    st.sidebar.header("Filtres")
    villes = sorted(df["city"].unique())
    selected_city = st.sidebar.selectbox("Sélectionne une ville principale :", villes)

    df_city = df[df["city"] == selected_city]

    # Plage de dates
    min_date = df_city["timestamp"].dt.date.min()
    max_date = df_city["timestamp"].dt.date.max()

    date_range = st.sidebar.date_input(
        "Période sélectionnée :",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    if len(date_range) == 2:
        start_d, end_d = date_range
        df_city = df_city[
            (df_city["timestamp"].dt.date >= start_d) & 
            (df_city["timestamp"].dt.date <= end_d)
        ]

    # KPIs sur les 30 jours
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🌡️ Température Moyenne", f"{round(df_city['temperature_celsius'].mean(), 1)} °C")
    col2.metric("🔥 Température Maximale", f"{round(df_city['temperature_celsius'].max(), 1)} °C")
    col3.metric("❄️ Température Minimale", f"{round(df_city['temperature_celsius'].min(), 1)} °C")
    col4.metric("💨 Vent Max", f"{round(df_city['wind_speed_kmh'].max(), 1)} km/h")

    st.divider()

    # Graphique 1 : Évolution de la ville choisie
    st.subheader(f"📈 Historique des températures à {selected_city}")
    fig_temp = px.line(
        df_city,
        x="timestamp",
        y="temperature_celsius",
        title=f"Relevés horaires ({selected_city})",
        labels={"timestamp": "Date & Heure", "temperature_celsius": "Température (°C)"}
    )
    fig_temp.update_traces(line_color="#FF4B4B")
    st.plotly_chart(fig_temp, use_container_width=True)

    # Graphique 2 : Comparateur personnalisable (sélectionner 2 à 5 villes pour comparer)
    st.subheader("🌍 Comparateur multi-villes sur 30 jours")
    villes_a_comparer = st.multiselect(
        "Choisis les villes à superposer sur le graphique :",
        options=villes,
        default=[selected_city, "Paris", "Marseille"] if "Marseille" in villes and "Paris" in villes else [selected_city]
    )
    
    if villes_a_comparer:
        df_comp = df[df["city"].isin(villes_a_comparer)]
        if len(date_range) == 2:
            df_comp = df_comp[
                (df_comp["timestamp"].dt.date >= start_d) & 
                (df_comp["timestamp"].dt.date <= end_d)
            ]
        fig_comp = px.line(
            df_comp,
            x="timestamp",
            y="temperature_celsius",
            color="city",
            title="Comparaison des relevés horaires",
            labels={"timestamp": "Date & Heure", "temperature_celsius": "Température (°C)", "city": "Ville"}
        )
        st.plotly_chart(fig_comp, use_container_width=True)

    with st.expander("🔍 Voir les données brutes"):
        st.dataframe(df_city, use_container_width=True)

except Exception as e:
    st.error(f"Erreur : {e}")