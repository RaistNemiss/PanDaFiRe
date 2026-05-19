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
            texte += page.extract_text() or ""
    
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

        date = date_parse(candidat, settings=parse_settings)
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

    mot_exclus = ("facture", "reçu", "date", "montant", "rappel", "référence", "concerne", "client", "invoice", "Madame", "Monsieur",)
    
    for ligne in lignes_texte[:15]:  # on se concentre sur les premières lignes du document
        l = ligne.strip() #supprime les espaces et/ou tabulation en début et fin de ligne
        l_minusucule = l.lower()
    
        if any(exclu in l_minusucule for exclu in mot_exclus):
            continue

        if (
            6 <= len(l) <= 60 # longueur raisonnable pour un nom d'émetteur
            and any(c.isupper() for c in l)  # au moins une majuscule   
            and not re.search(r"\d", l)  # pas de chiffres
        ):
            candidats.append(l)
    
    return candidats

def extraire_noms_societes(texte: str) -> list:
    
    suffixes_sociaux = ["sa", "sas", "sarl", "eurl", "gmbh", "ltd", "inc", "corp", "co", "scoop", "scop", "association", "fondation", "coopérative", "mutuelle"]
    
    lignes_texte = texte.split("\n")
    candidats = []

    
    for ligne in lignes_texte[:15]:  # on se concentre sur les premières lignes du document
        mots = ligne.split()

        tampon = []

        for mot in mots:
            mot_clean = mot.strip(".,()[]-_")
            
            if not mot_clean:
                continue

            # majuscule initiale
            est_majuscule_initiale = mot_clean[0].isupper()

            # forme juridique
            est_suffixe_social = mot_clean.lower() in suffixes_sociaux

            if est_majuscule_initiale or est_suffixe_social:
                tampon.append(mot_clean)
            else:
                #fin du groupe
                if len(tampon) >=2:
                    candidats.append(" ".join(tampon))
                tampon = []
        
        if len(tampon) >=2:
            candidats.append(" ".join(tampon))

    return candidats

def extraire_nom_sans_date(nom: str) -> str:

    nom_sans_dates = nom.lower()

    for regex in REGEX_DATES_CANDIDATS:
        nom_sans_dates = re.sub(regex, "", nom_sans_dates, flags=re.IGNORECASE)

    nom_sans_dates = re.sub(r"[._\-\s]+", "_", nom_sans_dates).strip("_ ")

    return nom_sans_dates

