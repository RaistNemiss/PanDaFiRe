import pdfplumber
import re
from datetime import datetime
from dateutil import parser
from pathlib import Path
from .ocr import extraire_texte_ocr


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
    annee_min = datetime.now().year - 5
    annee_max = datetime.now().year + 1
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
            if date.year < annee_min or date.year > annee_max:
                continue
            return date.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            continue
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