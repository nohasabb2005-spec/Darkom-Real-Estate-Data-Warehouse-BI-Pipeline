import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
import logging

import seaborn as sns
from datetime import datetime
from utils import *


# CONFIGURATION LOGGING

os.makedirs("logs", exist_ok=True)

from utils import *
import seaborn as sns
from datetime import datetime 


# LOGGING SAFE
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    filename="logs/clean.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


logging.info("Début du pipeline CLEAN.")


# LOAD ENV

load_dotenv()


load_dotenv()
# ENV VARIABLES

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASS = os.getenv("POSTGRES_PASSWORD")
DB_PORT = os.getenv("DB_PORT")


try:

  
    # CONNEXION DATABASE
 
    engine = create_engine(
        f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    logging.info("Connexion PostgreSQL réussie.")

    
    # EXTRACTION DATA
   
    query = "SELECT * FROM bronze.staging_darkom;"
    df = pd.read_sql(query, engine)

    logging.info(f"Données chargées : {df.shape[0]} lignes.")

    # DUPLICATES
    
    duplicates = df.duplicated().sum()

    logging.warning(f"Nombre de doublons détectés : {duplicates}")

    df = df.drop_duplicates(subset="annonce_id")

    logging.info(f"Shape après suppression doublons : {df.shape}")

   
    # VALEURS MANQUANTES
   
    taux_null = df.isnull().mean() * 100

    logging.info("Calcul des valeurs manquantes terminé.")

    # Visualisation
    taux_null.sort_values(ascending=False).plot(
        kind="barh",
        color="pink"
    )

    plt.title("Taux des valeurs manquantes")
    plt.xlabel("Pourcentage")
    plt.ylabel("Colonnes")

    plt.tight_layout()

    plt.savefig("logs/missing_values.png")
    plt.close()

   
    # TRAITEMENT VARIABLES CATEGORIELLES
  
    logging.info("Traitement des variables catégorielles.")

    df["quartier"] = (
        df.groupby("ville")["quartier"]
        .transform(fill_mode)
    )

    df["type_bien"] = (
        df.groupby("ville")["type_bien"]
        .transform(fill_mode)
    )

    df["transaction"] = (
        df.groupby(["ville", "type_bien"])["transaction"]
        .transform(fill_mode)
    )

    
    # VARIABLES NUMERIQUES
   
    num_cols = [
        "nb_salles_bain",
        "annee_construction",
        "nb_chambres",
        "etage"
    ]

    for col in num_cols:
        median_value = df[col].median()
        df[col] = df[col].fillna(median_value)

        logging.info(f"NaN remplacés dans {col} par médiane.")

   
    # DATE

    df["date_publication"] = pd.to_datetime(
        df["date_publication"],
        errors="coerce"
    )

    df["date_publication"] = df["date_publication"].ffill()

    logging.info("Transformation date_publication réussie.")

    # FEATURES TEMPORELLES
    df["annee"] = df["date_publication"].dt.year
    df["mois"] = df["date_publication"].dt.month
    df["trimestre"] = df["date_publication"].dt.quarter
    df["semaine"] = df["date_publication"].dt.isocalendar().week

    
    # OUTLIERS
  
    cols = ["prix", "surface", "nb_chambres"]

    df_clean = df.copy()

    for col in cols:

        Q1 = df_clean[col].quantile(0.25)
        Q3 = df_clean[col].quantile(0.75)

        IQR = Q3 - Q1

        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR

        before = df_clean.shape[0]

        df_clean = df_clean[
            (df_clean[col] >= lower)
            & (df_clean[col] <= upper)
        ]

        after = df_clean.shape[0]

        logging.info(
            f"Outliers supprimés pour {col} : {before - after}"
        )

   
    # STANDARDISATION
   
    df_clean["ville"] = df_clean["ville"].map(uniformiser)

    df_clean["type_bien"] = (
        df_clean["type_bien"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    df_clean["transaction"] = (
        df_clean["transaction"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    logging.info("Standardisation terminée.")

  
    # FEATURE ENGINEERING
  
    df_clean["prix_m2"] = (
        df_clean["prix"] / df_clean["surface"]
    )

    df_clean["age_estime_bien_immobilier"] = (
        datetime.now().year
        - df_clean["annee_construction"]
    )

    df_clean["categorie_prix"] = pd.qcut(
        df_clean["prix"],
        q=4,
        labels=[
            "Economique",
            "Moyen",
            "Haut standing",
            "Luxe"
        ]
    )

    # CORRECTION BUG
    df_clean["categorie_surface"] = (
        df_clean["surface"].apply(Catégories_surface)
    )

    logging.info("Feature engineering terminé.")

   
    df_clean["date_publication"] = pd.to_datetime(
        df_clean["date_publication"]
    ).dt.date

  
    if not df_clean.empty:

        df_clean.to_sql(
            "clean",
            engine,
            schema="silver",
            if_exists="append",
            index=False
        )

        logging.info(
            f"Données insérées dans silver.clean : {df_clean.shape}"
        )

    else:
        logging.warning("DataFrame vide. Aucune insertion.")

except Exception as e:

    logging.exception(f"Erreur dans pipeline clean : {e}")

finally:

    logging.info("Fin du pipeline CLEAN.")
