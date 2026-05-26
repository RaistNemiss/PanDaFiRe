from .config import charger_config_destinataires


def determiner_initiales_destinataire(nom: str) -> str:

    if not nom or nom == "inconnu":
        return ""

    # les noms du json sont normalisés avec des underscores
    mots = nom.split("_")

    if len(mots) == 2:
        # 1 lettre du prénom + 2 lettres du nom (ex: Homer Simpson → HSI)
        return (mots[0][:1] + mots[1][:2]).upper()

    if len(mots) == 1:
        # 2 premières lettres (ex: Homer → HO)
        return nom[:2].upper()

    # 1 lettre par mot (ex: Jean Claude Van Damme → JCVD)
    return "".join(mot[0] for mot in mots).upper()

def generer_keywords_destinataire(
        nom: str,
        prenom: str,
        email: str = "", 
        telephone: str = ""
        ) -> dict[str,int]:

    # Construction automatique des keywords avec poids
    nom_complet = f"{prenom} {nom}"
    keywords = {
        nom_complet.lower(): 5,   # nom complet → fort
        prenom.lower(): 1,        # prénom seul → faible
        nom.lower(): 1,           # nom seul → faible
    }
    if email:
        keywords[email.lower()] = 5
    if telephone:
        keywords[telephone] = 5
        
        # normalisation du téléphone pour maximiser les chances de correspondance (ex: "+41 77 777 77 77" → "41777777777")
        tel_normalise = "".join(c for c in telephone if c.isdigit())
        
        if tel_normalise:
            keywords[tel_normalise] = 3

        

    return keywords

def destinataire_existe(nom_complet: str) -> bool:

    destinataires = charger_config_destinataires()
    
    nom_complet_clean = nom_complet.lower().strip()
    
    return any(
        dest["description"].lower() == nom_complet_clean
        for dest in destinataires.values()
    )