import pandas as pd
import psycopg2
import logging
import os
from sqlalchemy import create_engine



os.makedirs("logs", exist_ok=True)


# LOGGING SAFE
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    filename="logs/staging.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("POSTGRES_DB", "darkom_dwh")
DB_USER = os.getenv("POSTGRES_USER", "user")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "Nouha12")
DB_PORT = os.getenv("DB_PORT", "5432")

try:
  
    engine = create_engine(
        f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    logging.info("Connexion à PostgreSQL réussie.")

   
    file_path = "data/darkom-annonces.csv"

    df = pd.read_csv(file_path)

    logging.info(f"Fichier CSV chargé avec succès : {file_path}")
    logging.info(f"Nombre de lignes : {len(df)}")

   
    df.to_sql(
        "staging_darkom",
        engine,
        if_exists="append",
        schema="bronze",
        index=False
    )

    logging.info("Insertion des données dans bronze.staging_darkom réussie.")

except FileNotFoundError:
    logging.error("Le fichier CSV est introuvable.")

except psycopg2.Error as db_error:
    logging.error(f"Erreur PostgreSQL : {db_error}")

except Exception as e:
    logging.exception(f"Erreur inattendue : {e}")
