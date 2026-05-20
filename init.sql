create schema if not exists bronze;
create table if not exists bronze.staging_darkom(
    annonce_id varchar(15),
    date_publication date,
    titre varchar(100),
    ville varchar(100),
    quartier varchar(40),
    type_bien varchar(40),
    transaction varchar(40),
    prix numeric(12,2),
    surface numeric(12,2),
    nb_chambres int,
    nb_salles_bain int,
    etage int,
    annee_construction int
);
create schema if not exists silver;

create table if not exists silver.clean(
    annonce_id varchar(15),
    date_publication date,
    titre varchar(100),
    ville varchar(40),
    quartier varchar(40),
    type_bien varchar(40),
    transaction varchar(40),
    prix numeric(12,2),
    surface numeric(12,2),
    nb_chambres int,
    nb_salles_bain int,
    etage int,
    annee_construction int,
    annee int,
    mois int,
    trimestre int,
    semaine int,
    prix_m2 numeric(12,2),
    age_estime_bien_immobilier int,
    categorie_prix varchar(40),
    categorie_surface varchar(40)
);
create schema if not exists gold;
create table if not exists gold.dim_temps(
    date_id varchar(15) primary key,
    date_publication date,
    annee int,
    mois int,
    trimestre int,
    semaine int
);

create table if not exists gold.dim_type_bien(
    type_bien_id varchar(15) primary key,
    type_bien varchar(40),
    categorie varchar(100)
);

create table if not exists gold.dim_categorie_prix(
    categorie_prix_id varchar(15) primary key,
    categorie_prix varchar(30) 
);

create table if not exists gold.dim_transaction(
    transaction_id varchar(40) primary key,
    transaction varchar(40)
);

create table if not exists gold.dim_ville(
    ville_id varchar(40) primary key,
    ville varchar(40)
);

create table if not exists gold.dim_quartier(
    quartier_id varchar(40) primary key,
    quartier varchar(40),
    ville_id varchar(40) references gold.dim_ville(ville_id)
);

create table if not exists gold.fact_annonces(
    annonce_id varchar(40) primary key,
    date_id varchar(15),
    ville_id varchar(40),
    quartier_id varchar(40),
    type_bien_id varchar(15),
    transaction_id varchar(40),
    categorie_prix_id varchar(15),
    prix numeric(12,2),
    surface numeric(12,2),
    nb_chambres int,
    nb_salles_bain int,
    etage int,
    prix_m2 numeric(12,2),
    age_estime_bien_immobilier int,
    FOREIGN KEY (date_id) REFERENCES gold.dim_temps(date_id),
    FOREIGN KEY (ville_id) REFERENCES gold.dim_ville(ville_id),
    FOREIGN KEY (quartier_id) REFERENCES gold.dim_quartier(quartier_id),
    FOREIGN KEY (type_bien_id) REFERENCES gold.dim_type_bien(type_bien_id),
    FOREIGN KEY (transaction_id) REFERENCES gold.dim_transaction(transaction_id),
    FOREIGN KEY (categorie_prix_id) REFERENCES gold.dim_categorie_prix(categorie_prix_id)
);

