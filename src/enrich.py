import json
from pathlib import Path
from collections import Counter
import unicodedata
import re

ARTICLES_PREPOSITIONS = r"\b(de|du|la|des|le|les|et|à|au|aux)\b"

def candidats_frequents(logs: list[dict]) -> list[tuple[str, int]]:

    emetteurs = []
    seuil_occurrence = (
        5  # seuil de fréquence pour considérer un candidat comme pertinent
    )

    for log in logs:
        emetteurs.extend(log.get("emetteur_candidats", []))

    counter = Counter(emetteurs)

    return [
        (emetteur, occurrence)
        for emetteur, occurrence in counter.most_common()
        if occurrence >= seuil_occurrence
    ]

def ajouter_emetteur_json(
    emetteur_select: str, categorie_emetteur: str, emetteur_json_path: Path
) -> None:

    nouveau_emetteur = emetteur_select.strip()
    nouvelle_clef_emetteur = normaliser_nom(nouveau_emetteur).replace(" ", "_")

    nouvelle_entree = {
        "description": nouveau_emetteur,
        "category": categorie_emetteur,
        "keywords": genener_mot_clef(nouveau_emetteur)
    }

    with open(emetteur_json_path, "r", encoding="utf-8") as f:
        data_emetteurs = json.load(f)

    if nouvelle_clef_emetteur in data_emetteurs:
        print(f"⚠️ L'émetteur '{nouveau_emetteur}' existe déjà dans la configuration.")
        return

    data_emetteurs[nouvelle_clef_emetteur] = nouvelle_entree

    with open(emetteur_json_path, "w", encoding="utf-8") as f:
        json.dump(data_emetteurs, f, indent=4, ensure_ascii=False)

    print(f"✅ Émetteur ajouté : {nouvelle_clef_emetteur}")

    return

def genener_mot_clef(nom: str) -> dict:

    nom_clean = nom.lower().strip()

    keywords = {}

    #nom exact
    keywords[nom_clean] = 5

    #nom sans espaces
    nom_sans_espaces = nom_clean.replace(" ", "")
    if nom_sans_espaces != nom_clean:
        keywords[nom_sans_espaces] = 4

    # mots significatifs du nom (ex: "Société Générale" → "Société", "Générale", "SociétéGénérale") pour maximiser les chances de correspondance même si le nom complet n'est pas mentionné dans le document
    mots_significatifs = extraire_mot_significatif(nom)
    for mot in mots_significatifs:
        if mot not in keywords:
            keywords[mot] = 1

    # enlever "de", "du", "la" → version simplifiée
    nom_simple = re.sub(ARTICLES_PREPOSITIONS, "", nom_clean)
    nom_simple = re.sub(r"\s+", " ", nom_simple).strip()

    if nom_simple != nom_clean:
        keywords[nom_simple] = 4

    # version sans accents (ex: "café" → "cafe") OCR utile
    nom_sans_accents = enlever_accents(nom_clean)
    if nom_sans_accents != nom_clean:
        keywords[nom_sans_accents] = 2

    # version sans espaces (ex: "Société Générale" → "SociétéGénérale") OCR utile
    nom_sans_espaces = nom_clean.replace(" ", "")
    if nom_sans_espaces != nom_clean:
        keywords[nom_sans_espaces] = 4

    return keywords

def extraire_mot_significatif(nom: str) -> list[str]:
    mots = nom.split()

    candidats = []
    for mot in mots:
        mot_clean = mot.strip(".,()[]-_")

        # mot avec majuscules non initiales ou acronyme (UBS)
        if mot_clean and (
            (mot_clean[0].isupper() and not mot_clean.isupper())
            or (len(mot_clean) <= 4 and mot_clean.isupper())
        ):

            candidats.append(mot_clean.lower())
    
    return candidats

def normaliser_nom(nom: str) -> str:
    nom_normalise = nom.lower().strip()
    

    # enlever les articles et prépositions courants
    nom_normalise = re.sub(ARTICLES_PREPOSITIONS, "", nom_normalise)
    
    # enlever les accents
    nom_normalise = enlever_accents(nom)

    # nettoyer les espaces
    nom_normalise = re.sub(r"\s+", " ", nom_normalise).strip()
    return nom_normalise

def enlever_accents(nom: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", nom)
        if unicodedata.category(c) != "Mn"
    )