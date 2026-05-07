import pdfplumber
import re
from datetime import datetime
from dateutil import parser
from pathlib import Path
from .ocr import extraire_texte_ocr



CONFIG_DOCUMENTS_PATH = Path(r"logs\types_documents.json")
EMETTEURS_PATH = Path(r"logs\emetteurs.json")
REGEX_DATES_CANDIDATS = [
    r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b",   # 12/04/2024, 12-04-24
    r"\b\d{4}[./-]\d{1,2}[./-]\d{1,2}\b",     # 2024-04-12
    r"\b\d{1,2}\s+[a-zA-Zéû]+\s+\d{4}\b",     # 12 avril 2024
    r"\b[a-zA-Z]+\s+\d{1,2},?\s+\d{4}\b",     # April 12, 2024
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
    for regex in REGEX_DATES_CANDIDATS:
        candidats.extend(re.findall(regex, texte))
    for candidat in candidats:
        try:
            date = parser.parse(
                candidat,
                dayfirst=True,   # IMPORTANT en contexte européen
                fuzzy=True
            )
        # Vérification de la plausibilité de la date (ex: pas dans le futur lointain ou trop ancien)
            if date.year < 1900 or date.year > datetime.now().year + 1:
                continue
            return date.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            continue
    # Aucun parsing réussi → date du jour
    return datetime.today().strftime("%Y-%m-%d")

def extraire_candidats_emetteur(texte: str) -> list:
    
    lignes_texte = texte.split("\n")
    candidats = []

    mot_exclus = ("facture", "reçu", "date", "montant", "rappel", "référence", "concerne", "client", "invoice")
    
    for ligne in lignes_texte[:15]:  # on se concentre sur les premières lignes du document
        l = ligne.strip()
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

# def extraire_emetteur(texte: str, retour_score: bool = False):
#     with open(EMETTEURS_PATH, "r", encoding="utf-8") as f:
#         EMETTEURS = json.load(f)
#     treshold = 5
#     return identifier_par_score(texte, EMETTEURS, seuil=treshold, retour_score=retour_score)

# def extraire_type_document(texte: str, retour_score: bool = False):
#     with open(CONFIG_DOCUMENTS_PATH, "r", encoding="utf-8") as f:
#         TYPES_DOCUMENTS = json.load(f)
#     treshold = 4
#     return identifier_par_score(texte, TYPES_DOCUMENTS, seuil=treshold, retour_score=retour_score)

