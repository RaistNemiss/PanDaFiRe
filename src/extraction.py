import pdfplumber
import re
from datetime import datetime
from dateparser import parse as date_parse
from pathlib import Path
from .ocr import extraire_texte_ocr


REGEX_DATES_CANDIDATS = [
    r"\b\d{1,2}[./-_]\d{1,2}[./-_]\d{2,4}\b",   # 12/04/2024, 12-04-24
    r"\b\d{4}[./-_]\d{1,2}[./-_]\d{1,2}\b",     # 2024-04-12
    r"\b\d{1,2}(?:er|ème)?\s+[A-Za-zÀ-ÿ]+\s+\d{2,4}\b",     # 12 avril 2024, 1er mai 2025
    r"\b[A-Za-zÀ-ÿ]+\s+\d{1,2}(?:er|ème)?,?\s+\d{2,4}\b",     # April 12, 2024, avril 12, 2024
]


def extraire_texte(pdf_path: Path) -> tuple[str, bool]:
    
    texte = ""
    
    with pdfplumber.open(pdf_path) as pdf:   
        for page in pdf.pages:
            # extract_text() peut retourner None si la page est vide ou si le texte ne peut pas être extrait (ex: PDF scanné)
            texte = "\n".join(page.extract_text() or "" for page in pdf.pages)
    
    if texte.strip():
        return texte, False  # texte extrait avec succès, pas besoin d'OCR
        
    print(f"🔍 {pdf_path.name} PDF scanné détecté → OCR")
    texte = extraire_texte_ocr(pdf_path)

    return texte, True  # texte extrait via OCR

def extraire_date_document(texte: str) -> str:
    texte = texte.lower()
    candidats = []
    annee_min = datetime.now().year - 5
    annee_max = datetime.now().year + 1

    for regex in REGEX_DATES_CANDIDATS:
        candidats.extend(re.findall(regex, texte))

    for candidat in candidats:
        candidat = re.sub(r"\b(\d{1,2})(?:er|ème|eme)\b", r"\1", candidat, flags=re.IGNORECASE)
        parse_settings = {
            "STRICT_PARSING": True,
            "DATE_ORDER": "DMY",  # par défaut, on suppose jour-mois-année
        }
        if re.match(r"^\d{4}[./-]\d{1,2}[./-]\d{1,2}$", candidat):
            # Format année-mois-jour clair
            parse_settings["DATE_ORDER"] = "YMD"
        date = date_parse(candidat, settings=parse_settings) # type: ignore
        if not date:
            continue
        # Vérification de la plausibilité de la date (ex: pas dans le futur lointain ou trop ancien)
        if date.year < annee_min or date.year > annee_max:
            continue
        return date.strftime("%Y-%m-%d")
    
    # Aucun parsing réussi → date du jour
    return datetime.today().strftime("%Y-%m-%d")

def extraire_candidats_emetteur(texte: str) -> list:
    
    lignes_texte = texte.split("\n")
    candidats = []

    mot_exclus = ("facture", "reçu", "date", "montant", "rappel",
                   "référence", "concerne", "client", "invoice",
                     "Madame", "Monsieur", "objet",)
    
    for ligne in lignes_texte[:15]:  # on se concentre sur les premières lignes du document
        l = ligne.strip() #supprime les espaces et/ou tabulation en début et fin de ligne
        l_minusucule = l.lower()
    
        # Filtre 1 : mots exclus
        if any(exclu in l_minusucule for exclu in mot_exclus):
            continue
        
        # Filtre 2 : longueur raisonnable
        if not (6 <= len(l) <= 60):
            continue

        # Filtre 3 : pas de chiffres
        if re.search(r"\d", l):
            continue

        # Filtre 4 : ratio de mots avec majuscules
        mots = [m.strip(".,") for m in l.split() if len(m) > 1] # exclut les lettres isolées.

        if not mots:
            continue

        #somme du nombre de mots avec une majuscule initiale
        nombre_mots_majuscule = sum(1 for m in mots if m[0].isupper())
        #calcul du ratio de mots avec majuscules par rapport au nombre total de mots
        ratio_majuscule = nombre_mots_majuscule / len(mots)

        if ratio_majuscule < 0.5:
            continue

        candidats.append(l)
    
    return candidats

def extraire_noms_societes(texte: str) -> list:
    
    # Liste des formes juridiques reconnues (en minuscules pour comparaison)
    suffixes_sociaux = [
        # 🇨🇭 Allemand
        "ag", "gmbh", "eg",
        # 🇨🇭 Français
        "sa", "sàrl", "sarl",
        # 🇨🇭 Italien
        "spa", "srl",
        # 🇬🇧🇺🇸 Anglais
        "ltd", "llc", "inc", "corp", "plc", "co",
        # 🇫🇷 France (bonus, fréquent dans les docs)
        "sas", "eurl", "scop", "scoop",
        # Autres
        "fondation", "association", "coopérative", "mutuelle",
        ]
    
    lignes_texte = texte.split("\n")
    candidats = []

    
    for ligne in lignes_texte[:15]:  # on se concentre sur les premières lignes du document
        mots = ligne.split()

        tampon = [] # accumule les mots majuscules consécutifs

        for mot in mots:
            mot_clean = mot.strip(".,()[]-_")
            
            if not mot_clean:
                continue

            # Le mot commence-t-il par une majuscule ?
            est_majuscule_initiale = mot_clean[0].isupper()

            # Le mot est-il une forme juridique ?
            if len(mot_clean) <= 2 and mot_clean.isupper():
                # "SA", "AG" → seulement si en majuscules
                est_suffixe_social = mot_clean.lower() in suffixes_sociaux
            elif len(mot_clean) > 2:
                # "SARL", "GmbH", "Ltd" → peu importe la casse
                est_suffixe_social = mot_clean.lower() in suffixes_sociaux
            else:
                est_suffixe_social = False

            if est_suffixe_social and tampon:
                # ✅ On a trouvé une société : "Tampon + suffixe"
                nom_societe = " ".join(tampon) + " " + mot_clean
                candidats.append(nom_societe)
                tampon = []  # réinitialise le tampon pour chercher une nouvelle société

            elif est_majuscule_initiale:
                # mot majuscule isolé → potentiel candidat (ex: "UBS")
                candidats.append(mot_clean)

            else:
                # mot en miniscule, réinitialise le tampon pour qu'il disparaisse du candidat potentiel
                tampon = []

    return candidats

def extraire_nom_pdf_sans_date(nom: str) -> str:

    nom_sans_dates = nom.lower()

    for regex in REGEX_DATES_CANDIDATS:
        nom_sans_dates = re.sub(regex, "", nom_sans_dates, flags=re.IGNORECASE)

    nom_sans_dates = re.sub(r"[._\-\s]+", "_", nom_sans_dates).strip("_ ")

    return nom_sans_dates