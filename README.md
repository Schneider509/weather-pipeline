# 🌤️ Weather Data Pipeline & Analytics Dashboard

Pipeline ETL complet et tableau de bord interactif pour collecter, stocker et analyser les relevés météorologiques horaires des 50 plus grandes métropoles françaises sur 30 jours consolidés.

---

## 🏗️ Architecture et Fonctionnement

```text
weather-pipeline/
├── docker-compose.yml   # Déploiement du conteneur PostgreSQL 15
├── etl.py               # Extraction API, géocodage, transformation et Upsert
├── app.py               # Dashboard interactif Streamlit & visualisations Plotly
├── requirements.txt     # Dépendances Python verrouillées
├── .env.example         # Gabarit des identifiants et variables d'environnement
├── .gitignore           # Exclusion du dossier .venv et du fichier .env
└── README.md            # Documentation opérationnelle du projet
```

* **Extraction & Géocodage :** Récupération dynamique des coordonnées GPS des 50 villes puis appel à l'API d'archive Open-Meteo pour extraire 30 jours d'historique horaire consolidé.
* **Stockage Idempotent :** PostgreSQL 15 orchestré via Docker Compose. Les insertions reposent sur une contrainte d'unicité `PRIMARY KEY (city, timestamp)` et un pattern `INSERT ... ON CONFLICT DO UPDATE` (Upsert), évitant tout doublon en cas de réexécution.
* **Visualisation Analytique :** Application web Streamlit connectée à la base de données locale avec filtres temporels, KPIs et comparateur multi-villes.

---

## 📋 Prérequis

Assurez-vous que les outils suivants sont installés sur votre machine hôte :
* **Python 3.10+**
* **Docker Desktop** (avec Docker Compose actif)
* **Git**

---

## 🚀 Guide de Démarrage Rapide

### 1. Cloner le dépôt
```bash
git clone <URL_DU_DEPOT_GITHUB>
cd weather-pipeline
```

### 2. Configurer l'environnement virtuel Python
Créez un environnement isolé pour éviter tout conflit de dépendances avec votre système :
```bash
# Création de l'environnement virtuel
python3 -m venv .venv

# Activation sous macOS / Linux :
source .venv/bin/activate

# Activation sous Windows (PowerShell) :
# .venv\Scripts\Activate.ps1
```

### 3. Installer les dépendances
Installez les paquets requis via `pip` :
```bash
pip install -r requirements.txt
```

---

## ⚙️ Configuration des Variables d'Environnement

Créez votre fichier local `.env` en dupliquant le modèle fourni :
```bash
cp .env.example .env
```

### Détail des paramètres requis :

| Paramètre | Rôle | Valeur locale par défaut |
| :--- | :--- | :--- |
| `DB_USER` | Identifiant administrateur configuré dans `docker-compose.yml`. | `dev_user` |
| `DB_PASSWORD` | Mot de passe associé au compte administrateur. | `dev_password` |
| `DB_HOST` | Hôte du serveur (utilisez `localhost` pour Docker en local). | `localhost` |
| `DB_PORT` | Port d'écoute exposé sur la machine hôte. | `5432` |
| `DB_NAME` | Nom de la base de données créée à l'initialisation du conteneur. | `weather_db` |

---

## 🐳 Démarrer la Base de Données (Docker)

Lancez l'instance PostgreSQL en arrière-plan :
```bash
docker compose up -d
```

Vérifiez l'état d'exécution du conteneur :
```bash
docker compose ps
```

---

## 🔄 Lancer le Pipeline d'Ingestion (ETL)

Exécutez le script d'extraction et d'ingestion :
```bash
python etl.py
```

Le script réalise les opérations suivantes :
1. Géocodage des 50 métropoles françaises via l'API Open-Meteo.
2. Téléchargement des séries temporelles horaires des 30 derniers jours (température, humidité, vent).
3. Normalisation et typage strict des données avec `pandas`.
4. Ingestion résiliente de plus de **37 000 lignes** via table de staging et fusion Upsert.

Pour contrôler le nombre de lignes insérées directement dans PostgreSQL :
```bash
docker exec -it weather_postgres psql -U dev_user -d weather_db -c "SELECT city, COUNT(*) FROM cities_weather GROUP BY city LIMIT 10;"
```

---

## 📊 Lancer le Dashboard Analytique (Streamlit)

Démarrez l'application web locale :
```bash
streamlit run app.py
```

L'application s'ouvre automatiquement dans votre navigateur à l'adresse :  
👉 `http://localhost:8501`

### Fonctionnalités du tableau de bord :
* Sélecteur de ville avec affichage des métriques clés (température moyenne, extrêmes, rafales maximales).
* Filtre dynamique sur la plage de dates.
* Graphique temporel interactif des relevés heure par heure.
* Comparateur permettant de superposer les courbes de plusieurs villes simultanément.
* Visualisation tabulaire des données brutes stockées dans PostgreSQL.

---

## 🛑 Procédure d'Arrêt

* **Arrêter Streamlit :** Cliquez dans le terminal où tourne l'application et tapez `Ctrl + C`.
* **Mettre en pause la base PostgreSQL (sans perte de données) :**
  ```bash
  docker compose stop
  ```
* **Redémarrer la base ultérieurement :**
  ```bash
  docker compose start
  ```
* **Désactiver l'environnement virtuel Python :**
  ```bash
  deactivate
  ```