def fill_mode(x):
    m = x.mode()
    if not m.empty:
        return x.fillna(m.iloc[0])
    return x


info = {
    "casa": "casablanca",
    "casablanca": "casablanca",

    "meknès": "meknès",
    "meknes": "meknès",

    "rabat": "rabat",
    "kenitra": "kenitra",
    "kénitra": "kenitra",

    "tanger": "tanger",

    "fès": "fès",
    "fes": "fès",

    "oujda": "oujda",

    "agadir": "agadir",

    "marrakech": "marrakech",

    "tétouan": "tétouan",
    "tetouan": "tétouan"
}

def uniformiser(x):
    x = str(x).strip().lower()
    return info.get(x, x)  # garde la valeur originale si pas trouvée



def Catégories_prix(prix):
    if prix>4500000:
         return "Luxe"
    elif 2600000<prix<4500000:
        return "Haut standing"
    elif prix<2600000:
        return "Moyen"
    else:
        return "Économique"
    

def Catégories_surface(surface):
    if surface < 80:
        return "Petit"
    elif 80< surface < 150:
        return "Moyen"
    else:
        return "Grand"