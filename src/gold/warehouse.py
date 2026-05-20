import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
import logging


# LOGGING

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    filename="logs/warehouse.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logging.info("Début pipeline GOLD.")


# LOAD ENV

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASS = os.getenv("POSTGRES_PASSWORD")
DB_PORT = os.getenv("DB_PORT")

try:

    
    # DATABASE CONNECTION
   
    engine = create_engine(
        f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    logging.info("Connexion PostgreSQL réussie.")

  
    # RESET SCHEMA GOLD
   
    with engine.connect() as conn:

        conn.execute(text(
            "DROP SCHEMA IF EXISTS gold CASCADE;"
        ))

        conn.execute(text(
            "CREATE SCHEMA gold;"
        ))

        conn.commit()

    logging.info("Schema GOLD recréé.")

    
    # LOAD SILVER DATA
   
    query = "SELECT * FROM silver.clean;"

    df = pd.read_sql(query, engine)

    logging.info(f"Données SILVER chargées : {df.shape}")

    
    # DIM TEMPS

    logging.info("Création dim_temps.")

    dim_temps = (
        df[[
            'date_publication',
            "annee",
            "mois",
            "trimestre",
            "semaine"
        ]]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    dim_temps['date_id'] = (
        "DA" + (dim_temps.index + 1).astype(str)
    )

    dim_temps = dim_temps[[
        "date_id",
        "date_publication",
        "annee",
        "mois",
        "trimestre",
        "semaine"
    ]]

    dim_temps.to_sql(
        "dim_temps",
        engine,
        schema="gold",
        if_exists="append",
        index=False
    )

   
    # DIM TYPE BIEN
   
    logging.info("Création dim_type_bien.")

    dim_type_bien = (
        df[['type_bien', 'categorie_surface']]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    dim_type_bien['type_bien_id'] = (
        "TB" + (dim_type_bien.index + 1).astype(str)
    )

    dim_type_bien = dim_type_bien[[
        "type_bien_id",
        "type_bien",
        "categorie_surface"
    ]]

    dim_type_bien.to_sql(
        "dim_type_bien",
        engine,
        schema='gold',
        if_exists="append",
        index=False
    )

    # DIM CATEGORIE PRIX
  
    logging.info("Création dim_categorie_prix.")

    dim_categorie_prix = (
        df[["categorie_prix"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    dim_categorie_prix['categorie_prix_id'] = (
        "CP" + (dim_categorie_prix.index + 1).astype(str)
    )

    dim_categorie_prix.to_sql(
        "dim_categorie_prix",
        engine,
        schema='gold',
        if_exists='append',
        index=False
    )

    
    # DIM TRANSACTION

    logging.info("Création dim_transaction.")

    dim_transaction = (
        df[["transaction"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    dim_transaction["transaction_id"] = (
        "TR" + (dim_transaction.index + 1).astype(str)
    )

    dim_transaction.to_sql(
        "dim_transaction",
        engine,
        schema='gold',
        if_exists='append',
        index=False
    )

    
    # DIM VILLE
    
    logging.info("Création dim_ville.")

    dim_ville = (
        df[['ville']]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    dim_ville['ville_id'] = (
        "VILLE" + (dim_ville.index + 1).astype(str)
    )

    dim_ville.to_sql(
        "dim_ville",
        engine,
        schema='gold',
        if_exists='append',
        index=False
    )

  
    # DIM QUARTIER

    logging.info("Création dim_quartier.")

    dim_quartier = (
        df[['quartier', 'ville']]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    dim_quartier['quartier_id'] = (
        "QUARTIER" + (dim_quartier.index + 1).astype(str)
    )

    dim_quartier = dim_quartier.merge(
        dim_ville,
        on='ville',
        how='left'
    )

    dim_quartier = dim_quartier[[
        "quartier_id",
        "quartier",
        "ville_id"
    ]]

    dim_quartier.to_sql(
        "dim_quartier",
        engine,
        schema='gold',
        if_exists='append',
        index=False
    )

    # FACT TABLE
  
    logging.info("Création fact_annonces.")

    fact_annonces = (
        df[[
            'annonce_id',
            'date_publication',
            'ville',
            'quartier',
            'type_bien',
            'transaction',
            'categorie_prix',
            'prix',
            'surface',
            'nb_chambres',
            'nb_salles_bain',
            'etage',
            'prix_m2',
            'age_estime_bien_immobilier'
        ]]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    # ================= MERGES =================

    fact_annonces = fact_annonces.merge(
        dim_temps[['date_publication', 'date_id']],
        on='date_publication',
        how='left'
    )

    fact_annonces = fact_annonces.merge(
        dim_ville[['ville', 'ville_id']],
        on='ville',
        how='left'
    )

    fact_annonces = fact_annonces.merge(
        dim_quartier[['quartier', 'quartier_id']],
        on='quartier',
        how='left'
    )

    fact_annonces = fact_annonces.merge(
        dim_type_bien[['type_bien', 'type_bien_id']],
        on='type_bien',
        how='left'
    )

    fact_annonces = fact_annonces.merge(
        dim_transaction[['transaction', 'transaction_id']],
        on='transaction',
        how='left'
    )

    fact_annonces = fact_annonces.merge(
        dim_categorie_prix[
            ['categorie_prix', 'categorie_prix_id']
        ],
        on='categorie_prix',
        how='left'
    )

    
    # FINAL FACT TABLE
 
    fact_annonces = fact_annonces[[
        'annonce_id',
        'date_id',
        'ville_id',
        'quartier_id',
        'type_bien_id',
        'transaction_id',
        'categorie_prix_id',
        'prix',
        'surface',
        'nb_chambres',
        'nb_salles_bain',
        'etage',
        'prix_m2',
        'age_estime_bien_immobilier'
    ]].drop_duplicates()

    logging.info(
        f"Fact table créée : {fact_annonces.shape}"
    )

    fact_annonces.to_sql(
        'fact_annonces',
        engine,
        schema='gold',
        if_exists='append',
        index=False
    )

    logging.info("Chargement GOLD terminé avec succès.")

except Exception as e:

    logging.exception(f"Erreur pipeline GOLD : {e}")

finally:

    logging.info("Fin pipeline GOLD.")