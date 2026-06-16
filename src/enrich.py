""" Fonctions pour enrichir les émetteurs des données extraites. """

from collections import Counter
import re
from .utils import (
    ARTICLES_PREPOSITIONS,
    enlever_accents,
    ajuster_score_keywords_ambigus,
)
from .config import charger_config_emetteurs, categorie_disponible


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


def candidats_emetteur_a_traiter(logs: list[dict]) -> tuple[list, list]:

    # 1. recherche les possibles candidats fréquents dans les logs
    candidats = candidats_frequents(logs)
    
    # 2. charge les emetteurs connu dans une liste
    emetteurs = charger_config_emetteurs()
    emetteurs_connus = set()
    for emetteur in emetteurs.values():
        emetteurs_connus.add(emetteur["description"].lower())
        emetteurs_connus.update(keyword.lower() for keyword in emetteur.get("keywords", {}))

    # 3. vérifie que les candidats emetteurs ne sont pas dans la liste des emetteurs connus:
    candidats = [c for c in candidats if c[0].lower() not in emetteurs_connus]

    # 4. charger les catégories disponible pour les emetteurs
    categories = categorie_disponible("emetteurs")

    return candidats, categories


def generer_keywords_depuis_nom(nom: str) -> dict[str, int]:

    nom_clean = nom.lower().strip()

    keywords = {}

    # nom exact
    keywords[nom_clean] = 5

    # nom sans espaces
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

    return keywords


def generer_keywords_emetteur(
    nom: str,
    email: str = "",
    site_web_a: str = "",
    site_web_b: str = "",
    telephone: str = "",
    mot_cle_supplementaire: str = "",
) -> tuple[dict[str, int], list[str]]:

    keywords = generer_keywords_depuis_nom(nom)

    if email:
        keywords[email.lower()] = 4
        domaine_email = "@" + email.split("@")[-1]
        keywords[domaine_email] = 2

    if site_web_a:
        keywords[site_web_a.lower()] = 4
    if site_web_b:
        keywords[site_web_b.lower()] = 4
    if telephone:
        keywords[telephone] = 5

        # normalisation du téléphone pour maximiser les chances de correspondance (ex: "+41 77 777 77 77" → "41777777777")
        tel_normalise = "".join(c for c in telephone if c.isdigit())

        if tel_normalise:
            keywords[tel_normalise] = 3

    if mot_cle_supplementaire:
        for mot in mot_cle_supplementaire.split(","):
            mot_clean = mot.strip().lower()
            if mot_clean and mot_clean not in keywords:
                keywords[mot_clean] = 1

    return ajuster_score_keywords_ambigus(
        keywords, config_json=charger_config_emetteurs(), exclure=nom
    )


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