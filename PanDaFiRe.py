""" PadFire - A simple automatic PDF rename script by Alex Farina """
from pathlib import Path
import pdfplumber
import re
import json
import pytesseract
from pdf2image import convert_from_path
from datetime import datetime
from dateutil import parser




DIR_PATH = Path(r"C:\Users\Raist Nemiss\Downloads\Documents")
POPPLER_PATH = r"C:\TEMP\poppler-26.02.0\Library\bin"
CONFIG_DOCUMENTS_PATH = Path("types_documents.json")
REGEX_DATES_CANDIDATS = [
    r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b",   # 12/04/2024, 12-04-24
    r"\b\d{4}[./-]\d{1,2}[./-]\d{1,2}\b",     # 2024-04-12
    r"\b\d{1,2}\s+[a-zA-Zéû]+\s+\d{4}\b",     # 12 avril 2024
    r"\b[a-zA-Z]+\s+\d{1,2},?\s+\d{4}\b",     # April 12, 2024
]
pytesseract.pytesseract.tesseract_cmd = r"C:\TEMP\Tesseract-OCR\tesseract.exe"


def extraire_texte_pdf_ocr(pdf_path: Path) -> str:
    pages = convert_from_path(pdf_path, dpi=300, poppler_path=POPPLER_PATH)  # conversion du PDF en images à haute résolution pour une meilleure reconnaissance OCR
    texte = ""

    for page in pages:
        texte += pytesseract.image_to_string(page, lang="fra+eng", config="--oem 1 --psm 6") # configuration pour une meilleure reconnaissance de texte dans les documents structurés

    return texte

def extraire_texte_pdf(pdf_path: Path) -> tuple[str, bool]:
    
    texte = ""
    
    with pdfplumber.open(pdf_path) as pdf:   
        for page in pdf.pages:
            texte += page.extract_text() or ""
    
    if texte.strip():
        return texte, False  # texte extrait avec succès, pas besoin d'OCR
        
    print(f"🔍 {pdf_path.name} PDF scanné détecté → OCR")
    texte = extraire_texte_pdf_ocr(pdf_path)

    return texte, True  # texte extrait via OCR
    
def identifier_par_score(texte: str, config: dict, seuil: int = 4, retour_score: bool = False):
    # normalisation du texte pour faciliter la recherche
    texte = texte.lower()
    texte = re.sub(r"\s+", " ", texte)

    # création d'une compréhension de dictionnaire pour compter les occurrences de mots-clés pour chaque type de document
    scores = {cle: 0 for cle in config}

    for cle, data in config.items():
        mots_cle = data["mot_clef"]
        for mot, valeur_mot in mots_cle.items():
            if len(mot) < 3:  # éviter que les mots trop génère des faux positifs (ex: UBS dans sUBScription)
                nombre_occurrences = len(re.findall(rf"(!<?w){re.escape(mot)}(!?\w)", texte))
            else:
                nombre_occurrences = len(re.findall(rf"\b{re.escape(mot)}\b", texte))

            scores[cle] += nombre_occurrences * int(valeur_mot)
    gagnant = max(scores, key=scores.get)
    # seuil de confiance pour éviter les faux positifs
    resultat = gagnant if scores[gagnant] >= seuil else "inconnu"

    if retour_score:
        return resultat, scores
    
    return gagnant

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

def extraire_emetteur(texte: str, retour_score: bool = False):
    with open("emetteurs.json", "r", encoding="utf-8") as f:
        EMETTEURS = json.load(f)
    treshold = 5
    return identifier_par_score(texte, EMETTEURS, seuil=treshold, retour_score=retour_score)

def extraire_type_document(texte: str, retour_score: bool = False):
    with open(CONFIG_DOCUMENTS_PATH, "r", encoding="utf-8") as f:
        TYPES_DOCUMENTS = json.load(f)
    treshold = 4
    return identifier_par_score(texte, TYPES_DOCUMENTS, seuil=treshold, retour_score=retour_score)

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

def log_decision(pdf_path: Path, 
                 type_doc: str, 
                 type_doc_scores: dict,
                 emetteur: str, 
                 emetteur_scores: dict,
                 emetteur_candidats: list,
                 date_doc: str,
                 ocr_used: bool,
                 fichier_log="pandafire_decision_log.json",
                 ):
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "file": pdf_path.name,
        "type_document": type_doc,
        "type_document_scores": type_doc_scores,
        "emetteur": emetteur,
        "emetteur_scores": emetteur_scores,
        "emetteur_candidats": emetteur_candidats,
        "date_document": date_doc,
        "ocr_utilisé": ocr_used
    }

    with open(fichier_log, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

def main(pdf_path: Path):

    texte, ocr_utilise = extraire_texte_pdf(pdf_path)

    type_doc, type_doc_scores = extraire_type_document(texte, retour_score=True)
    date_doc = extraire_date_document(texte)
    emetteur, emetteur_scores = extraire_emetteur(texte, retour_score=True)

    if emetteur == "inconnu": # si l'émetteur n'est pas identifié avec suffisamment de confiance, on extrait des candidats potentiels pour analyse manuelle
        candidats_emetteur = extraire_candidats_emetteur(texte)
    else:
        candidats_emetteur = []


    log_decision(pdf_path, type_doc, type_doc_scores, emetteur, emetteur_scores, candidats_emetteur, date_doc, ocr_utilise)

    print(f"Le document {pdf_path.name} est identifié comme : {type_doc} - Emetteur du document : {emetteur} - Date extraite : {date_doc}")

if __name__ == "__main__":

    for pdf in DIR_PATH.glob("*.pdf"):
        main(pdf)
