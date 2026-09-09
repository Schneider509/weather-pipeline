# 🌤️ French Cities Weather Data Pipeline

Pipeline de données complet de bout en bout : extraction automatisée d'historiques météorologiques pour 50 villes françaises, stockage relationnel idempotent, orchestration avec Apache Airflow et restitution visuelle sur un tableau de bord conteneurisé.

---

## 🏗️ Architecture et Fonctionnement

```text
weather-pipeline/
├── dags/
│   └── weather_etl_dag.py   # Orchestration horaire Airflow
├── app.py                   # Dashboard analytique Streamlit & visualisations Plotly
├── etl.py                   # Extraction API, géocodage, transformation et Upsert
├── Dockerfile               # Conteneurisation de l'application Streamlit
├── docker-compose.yml       # Stack multi-conteneurs (Airflow, Postgres, Streamlit)
├── requirements.txt         # Dépendances Python verrouillées
├── .env.example             # Gabarit des variables d'environnement
├── .gitignore               # Fichiers et dossiers exclus du versionnement
└── README.md                # Documentation opérationnelle du projet
```

```text
[ Open-Meteo API ]
        │
        ▼ (Extraction horaire automatisée)
[ Apache Airflow DAG ] ───▶ [ Réseau Docker Interne ]
        │
        ▼ (Pattern Upsert idempotent)
[ PostgreSQL DB ] (cities_weather)
        │
        ▼ (Requêtes SQL avec cache)
[ Streamlit Dashboard ] ───▶ Navigateur (http://localhost:8501)
```

* **Extraction & Géocodage :** Récupération dynamique des coordonnées GPS des 50 métropoles françaises puis interrogation de l'API d'archive Open-Meteo pour extraire 30 jours d'historique horaire consolidé (température, humidité, vent).
* **Stockage Idempotent :** PostgreSQL 15 hébergé sous Docker. Les insertions reposent sur une clé primaire composite `(city, timestamp)` et une clause `ON CONFLICT DO UPDATE` (Upsert), garantissant l'absence de doublons même en cas de rattrapage ou réexécution.
* **Orchestration :** Apache Airflow 2.8 gère la planification horaire (`@hourly`), la surveillance des tâches et les politiques de réessai automatique.
* **Visualisation Analytique :** Application web Streamlit conteneurisée offrant des indicateurs clés (KPIs) en temps réel, des filtres dynamiques par ville et dates, des graphiques interactifs et une cartographie thermique nationale (`scatter_map`).

---

## 📋 Prérequis

* **Docker Desktop** (avec Docker Compose actif)
* **Git**

---

## 🚀 Déploiement Rapide (100 % Docker)

L'intégralité des services s'exécute dans des conteneurs isolés et communicants.

### 1. Cloner le dépôt
```bash
git clone [https://github.com/Schneider509/weather-pipeline.git](https://github.com/Schneider509/weather-pipeline.git)
cd weather-pipeline
```

### 2. Configurer les variables d'environnement
```bash
cp .env.example .env
```

### 3. Démarrer l'ensemble de la stack
```bash
docker compose up -d --build
```

Cette commande initialise et lance :
* **weather_postgres :** Base de données applicative météo (port `5432`).
* **airflow_postgres :** Base de métadonnées interne d'Airflow.
* **airflow_init :** Migration de schéma et création automatique de l'utilisateur admin.
* **airflow_webserver :** Interface d'administration Airflow (port `8080`).
* **airflow_scheduler :** Moteur d'exécution des DAGs.
* **weather_dashboard :** Tableau de bord Streamlit (port `8501`).

---

## 🖥️ Accès aux Interfaces

* **Dashboard Streamlit :** [http://localhost:8501](http://localhost:8501)
* **Console Apache Airflow :** [http://localhost:8080](http://localhost:8080)
  * **Identifiant :** `admin`
  * **Mot de passe :** `admin`

---

## 📊 Modèle de Données

Table : `cities_weather`

| Colonne | Type | Description |
| :--- | :--- | :--- |
| `city` | `VARCHAR` | Nom de la ville (*Clé primaire composite*) |
| `latitude` | `FLOAT` | Coordonnée GPS Nord |
| `longitude` | `FLOAT` | Coordonnée GPS Est |
| `timestamp` | `TIMESTAMP` | Horodatage de l'observation (*Clé primaire composite*) |
| `temperature_celsius` | `FLOAT` | Température relevée à 2 mètres (°C) |
| `humidity_percent` | `FLOAT` | Taux d'humidité relative (%) |
| `wind_speed_kmh` | `FLOAT` | Vitesse du vent à 10 mètres (km/h) |
| `extracted_at` | `TIMESTAMP` | Horodatage technique d'ingestion |

Pour contrôler le volume de données chargées :
```bash
docker exec -it weather_postgres psql -U dev_user -d weather_db -c "SELECT city, COUNT(*) FROM cities_weather GROUP BY city LIMIT 10;"
```

---

## 🛑 Arrêt et Maintenance

* **Mettre en pause l'ensemble des conteneurs (sans perte de données) :**
  ```bash
  docker compose stop
  ```
* **Redémarrer les services :**
  ```bash
  docker compose start
  ```
* **Arrêter et détruire les conteneurs :**
  ```bash
  docker compose down
  ```