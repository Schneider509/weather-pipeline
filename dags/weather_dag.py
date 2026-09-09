from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import sys

# Permet d'importer le script etl.py monté à la racine du conteneur
sys.path.append("/opt/airflow")
from etl import run_pipeline

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2026, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="weather_etl_pipeline",
    default_args=default_args,
    description="Pipeline ETL automatique pour les donnees meteo",
    schedule_interval="@hourly",  # S'exécute automatiquement chaque heure
    catchup=False,
    tags=["weather", "etl"],
) as dag:

    run_etl_task = PythonOperator(
        task_id="run_weather_etl",
        python_callable=run_pipeline,
    )

    run_etl_task