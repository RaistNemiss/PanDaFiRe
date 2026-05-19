import json
from pathlib import Path
from collections import Counter
import unicodedata
import re


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
    nouvelle_cle_emetteur = nouveau_emetteur.lower().replace(" ", "_")

    nouvelle_entree = {
        "description": nouveau_emetteur,
        "category": categorie_emetteur,
        "keywords": genener_mot_clef(nouveau_emetteur)
    }

    with open(emetteur_json_path, "r", encoding="utf-8") as f:
        data_emetteurs = json.load(f)

    if nouvelle_cle_emetteur in data_emetteurs:
        print(f"⚠️ L'émetteur '{nouveau_emetteur}' existe déjà dans la configuration.")
        return

    data_emetteurs[nouvelle_cle_emetteur] = nouvelle_entree

    with open(emetteur_json_path, "w", encoding="utf-8") as f:
        json.dump(data_emetteurs, f, indent=4, ensure_ascii=False)

    print(f"✅ Émetteur ajouté : {nouvelle_cle_emetteur}")

    return

def genener_mot_clef(nom: str) -> dict:
    nom_clean = nom.lower().strip()

    keywords = {
        nom_clean: 5,
        nom_clean.replace(" ", ""): 4,  # version sans espaces
    }

    # mots significatifs du nom (ex: "Société Générale" → "Société", "Générale", "SociétéGénérale") pour maximiser les chances de correspondance même si le nom complet n'est pas mentionné dans le document
    mots_significatifs = extraire_mot_significatif(nom)
    for mot in mots_significatifs:
        if mot not in keywords:
            keywords[mot] = 1

    # enlever "de", "du", "la" → version simplifiée
    nom_simple = re.sub(r"\b(de|du|la|des|le|les)\b", "", nom_clean)
    nom_simple = re.sub(r"\s+", " ", nom_simple).strip()

    if nom_simple != nom_clean:
        keywords[nom_simple] = 4

    # version sans accents (ex: "café" → "cafe") OCR utile
    nom_sans_accents = "".join(
        c
        for c in unicodedata.normalize("NFD", nom_clean)
        if unicodedata.category(c) != "Mn"
    )

    if nom_sans_accents != nom_clean:
        keywords[nom_sans_accents] = 2

    # version sans espaces (ex: "Société Générale" → "SociétéGénérale") OCR utile
    nom_sans_espaces = nom_clean.replace(" ", "")
    if nom_sans_espaces != nom_clean:
        keywords[nom_sans_espaces] = 2

    # première partie du nom (ex: "Société Générale" → "Société") pour les cas où seul le début du nom est mentionné
    partie_nom = nom_clean.split()
    if len(partie_nom) > 1:
        keywords[partie_nom[0]] = 3

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