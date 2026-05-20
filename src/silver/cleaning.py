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



engine = create_engine(
        f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}")


query="""select * from bronze.staging_darkom;"""
df=pd.read_sql(query,engine)

print(df.head())

print("===================")
print(df.info())

print("==============")
print(df.dtypes)
print("=======")
print(df.columns)
print("======================")
double=df.duplicated().sum()
print("Nombre des doublons: ",double)
df=df.drop_duplicates(subset="annonce_id")
print("les dimensions du df: ",df.shape)

print("=================")
taux_null=df.isnull().mean()*100
print(taux_null)

taux_null.sort_values(ascending=False).plot(kind="barh",color='pink')
plt.title("Taux des valeurs manquantes")
plt.xlabel("Pourcentage")
plt.ylabel("Colonnes")
plt.xticks(rotation=55)
plt.show()
print("=========================")
print("=============Traiter les valeurs manquantes===============")
print("////////Categories//////")
df["quartier"] = df.groupby("ville")["quartier"].transform(fill_mode)

df["type_bien"] = df.groupby("ville")["type_bien"].transform(fill_mode)

df["transaction"] = df.groupby(["ville", "type_bien"])["transaction"].transform(fill_mode)


print("////////////Numeriques/////")
num_cols = ["nb_salles_bain", "annee_construction", "nb_chambres", "etage"]

palette = sns.color_palette("Set2", len(num_cols))

plt.figure(figsize=(12,8))

for i, col in enumerate(num_cols):
    plt.subplot(2, 2, i+1)
    sns.histplot(df[col], bins=30, kde=True, color=palette[i])
    plt.title(f"Distribution de {col}")

plt.tight_layout()
plt.show()


df['nb_salles_bain']=df['nb_salles_bain'].fillna(df['nb_salles_bain'].median())
df['annee_construction']=df['annee_construction'].fillna(df['annee_construction'].median())
df['nb_chambres']=df['nb_chambres'].fillna(df['nb_chambres'].median())
df['etage']=df['etage'].fillna(df['etage'].median())


#df["date_publication"] = pd.to_datetime(df["date_publication"], errors="coerce")
#df["date_publication"] = df["date_publication"].fillna(pd.Timestamp("2026-01-01"))
df["date_publication"] = (
    pd.to_datetime(df["date_publication"], format='mixed')
      .ffill()
)
df["annee"] = df["date_publication"].dt.year
df["mois"] = df["date_publication"].dt.month
df["trimestre"] = df["date_publication"].dt.quarter
df["semaine"] = df["date_publication"].dt.isocalendar().week

taux_null=df.isnull().sum()
print(taux_null)


print("=============Outliers =============")

fig, axes = plt.subplots(1, 3, figsize=(18, 5))

axes[0].hist(df['prix'].dropna(), bins=20, color="#D5D7A6", edgecolor='black')
axes[0].set_title("prix")
axes[0].set_xlabel("prix")
# ================= SURFACE =================
axes[1].hist(df['surface'].dropna(), bins=20, color="#E93565", edgecolor='black')
axes[1].set_title("Surface")
axes[1].set_xlabel("Surface")

# ================= NB CHAMBRES =================
axes[2].hist(df['nb_chambres'].dropna(), bins=20, color="#A6C7D7", edgecolor='black')
axes[2].set_title("Nb chambres")
axes[2].set_xlabel("Nb chambres")

plt.tight_layout()
plt.show()

cols = ["prix", "surface", "nb_chambres"]

df_clean = df.copy()

for col in cols:
    Q1 = df_clean[col].quantile(0.25)
    Q3 = df_clean[col].quantile(0.75)
    IQR = Q3 - Q1

    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR

    df_clean = df_clean[(df_clean[col] >= lower) & (df_clean[col] <= upper)]

print("Shape avant :", df.shape)
print("Shape après :", df_clean.shape)


print("============Standardisation des données==========")
df_clean['ville']=df_clean['ville'].map(uniformiser)
df_clean["type_bien"] = df_clean["type_bien"].astype(str).str.strip().str.lower()
df_clean["transaction"] = df_clean["transaction"].astype(str).str.strip().str.lower()
unique=df_clean['ville'].unique()
print(unique)
print("================Feature Engineering=========")

df_clean['prix_m2']=df_clean['prix']/df_clean['surface']

df_clean["Age_estime_bien_immobilier"]=datetime.now().year - df_clean['annee_construction']

df_clean['categorie_prix']=pd.qcut(df_clean['prix'],q=4,labels=["Economique","Moyen","Haut standing","Luxe"])

df_clean["categorie_surface"]=df['surface'].apply(Catégories_surface)
print(df_clean.shape)

df_clean = df_clean.rename(columns={
    "Age_estime_bien_immobilier": "age_estime_bien_immobilier"
})

df_clean["date_publication"] = pd.to_datetime(
    df_clean["date_publication"]
).dt.date
df_clean.to_sql("clean",engine,schema="silver",if_exists='append',index=False)

