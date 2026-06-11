import pymupdf
import re
from datetime import datetime
from dateparser import parse as date_parse
from pathlib import Path

from .utils import ARTICLES_PREPOSITIONS
from .ocr import extraire_texte_ocr

# Pour le texte (corps du document)
REGEX_DATES_CANDIDATS = [
    r"\b\d{1,2}[./-_]\d{1,2}[./-_]\d{2,4}\b",   # 12/04/2024, 12-04-24
    r"\b\d{4}[./-_]\d{1,2}[./-_]\d{1,2}\b",     # 2024-04-12
    r"\b\d{1,2}(?:er|ème)?\s+[A-Za-zÀ-ÿ]+\s+\d{2,4}\b",     # 12 avril 2024, 1er mai 2025
    r"\b[A-Za-zÀ-ÿ]+\s+\d{1,2}(?:er|ème)?,?\s+\d{2,4}\b",     # April 12, 2024, avril 12, 2024
]

MOIS = r"(?:janvier|février|fevrier|mars|avril|mai|juin|juillet|août|aout|septembre|octobre|novembre|décembre|decembre)"

REGEX_DATES_CANDIDATS_FICHIER = [
    # Format JJ-MM-AAAA avec séparateurs . / - (ex: 12-04-2024, 12/04/24, 12.04.2024)
    r"(?<!\d)\d{1,2}[./-]\d{1,2}[./-]\d{2,4}(?!\d)",

    # Format AAAA-MM-JJ avec séparateurs . / - (ex: 2024-04-12, 2024/04/12, 2024.04.12)
    r"(?<!\d)\d{4}[./-]\d{1,2}[./-]\d{1,2}(?!\d)",

    # Format JJ_MM_AAAA avec underscores (ex: 12_04_2024, 12_04_24)
    r"(?<!\d)\d{1,2}_\d{1,2}_\d{2,4}(?!\d)",

    # Format AAAA_MM_JJ avec underscores (ex: 2024_04_12)
    r"(?<!\d)\d{4}_\d{1,2}_\d{1,2}(?!\d)",

    # Format JJ_mois_AAAA avec mois en texte, suffixe ordinal optionnel
    # (ex: 1er_mai_2023, 18_decembre_2023, 01er_mars_2022, 15_février_24)
    r"(?<!\d)\d{1,2}(?:er|ème)?_" + MOIS + r"_\d{2,4}(?!\d)",

    # Format mois_JJ_AAAA avec mois en texte au début
    # (ex: avril_12_2024, janvier_5_23)
    # Note : (?<!\w) ici car on ne veut PAS matcher si précédé d'une lettre
    # (sinon "rapport_avril_12_2024" serait matché à tort... mais ici on VEUT le matcher)
    r"(?<!\w)" + MOIS + r"_\d{1,2}_\d{2,4}(?!\d)",
]



def extraire_texte(pdf_path: Path) -> tuple[str, bool]:
    """Extrait le texte d'un PDF. Bascule sur OCR si le PDF est scanné."""
    with pymupdf.open(pdf_path) as pdf:   
        texte = "\n".join(page.get_text() for page in pdf.pages())
    
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
        ligne_clean = ligne.strip() #supprime les espaces et/ou tabulation en début et fin de ligne
        l_minusucule = ligne_clean.lower()
    
        # Filtre 1 : mots exclus
        if any(exclu in l_minusucule for exclu in mot_exclus):
            continue
        
        # Filtre 2 : longueur raisonnable
        if not (6 <= len(ligne_clean) <= 60):
            continue

        # Filtre 3 : pas de chiffres
        if re.search(r"\d", ligne_clean):
            continue

        # Filtre 4 : ratio de mots avec majuscules
        mots = [m.strip(".,") for m in ligne_clean.split() if len(m) > 1] # exclut les lettres isolées.

        if not mots:
            continue

        #somme du nombre de mots avec une majuscule initiale
        nombre_mots_majuscule = sum(1 for m in mots if m[0].isupper())
        #calcul du ratio de mots avec majuscules par rapport au nombre total de mots
        ratio_majuscule = nombre_mots_majuscule / len(mots)

        if ratio_majuscule < 0.5:
            continue

        candidats.append(ligne_clean)
    
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
        "fondation", "association", "coopérative", "mutuelle", "société", "holding",
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

            # Le mot ressemble-t-il à un nom de domaine ? (ex: "www.abc.com", "https://abc.com") → on peut extraire le nom de la société à partir du domaine
            if "www." in mot_clean or "http" in mot_clean:
                match = re.search(
                    r"(?:www\.|https?://)([\w-]+)\.\w+",
                    mot_clean,
                    re.IGNORECASE
                )
                if match:
                    candidats.append(match.group(1))
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
                # Accumule dans le tampon les mots avec majuscule initiale (pour capter "Café Lausanne SA")

                tampon.append(mot_clean)
                # Mot isolé : seulement les acronymes ALL CAPS (UBS, IKEA, BCV…)
                if (mot_clean.isupper() 
                    and len(mot_clean) >= 3 
                    and mot_clean.lower() not in ARTICLES_PREPOSITIONS):
                    candidats.append(mot_clean)

            else:
                # mot en miniscule, réinitialise le tampon pour qu'il disparaisse du candidat potentiel
                tampon = []

    return candidats

def extraire_nom_pdf_sans_date(nom_pdf: str) -> str:
    nom_sans_dates = nom_pdf.lower()

    for regex in REGEX_DATES_CANDIDATS_FICHIER:
        nom_sans_dates = re.sub(regex, "", nom_sans_dates, flags=re.IGNORECASE)

    nom_split = re.split(r"[._\-\s]+", nom_sans_dates)
    nom_split = [m for m in nom_split if m and m != "pdf"]

    return "_".join(nom_split).strip("_ ")


if __name__ == "__main__":

    fichiers_pdf = ["facture_12-04-2024_fournisseur.pdf",
    "2024.04.12_ordonnance_medecin.pdf",
    "releve_compte_2024_04_12.pdf",
    "scan_1er_mai_2023_contrat.pdf",
    "avril_12_2024_devis_client.pdf",
    "rapport_annuel_2023_bilan.pdf",
    "note_frais_12.04.24_remboursement.pdf",
    "contrat_15-03-2022_signature.pdf",
    "2022-03-15_facture_electricite.pdf",
    "devis_fournisseur_2024-12-18.pdf",
    "ordonnance_18_decembre_2023.pdf",
    "bulletin_salaire_janvier_2024.pdf",
    "12_04_2024_scan_document.pdf",
    "facture-2024-04-12-client.pdf",
    "releve_12/04/2024_banque.pdf",
    "2023_rapport_15_fevrier.pdf",
    "document_scan_03-2024.pdf",
    "facture_avril_2024_total.pdf",
    "contrat_01er_mars_2022.pdf",
    "bilan_2023.pdf",
    ]

    for nom in fichiers_pdf:
        nom_sans_date = extraire_nom_pdf_sans_date(nom)
        print(f"{nom} → {nom_sans_date}")
