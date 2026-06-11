from pathlib import Path
from collections import Counter
import re
import typer
from .utils import (
    ajouter_nouvelle_entree_json,
    ARTICLES_PREPOSITIONS,
    enlever_accents,
    ajuster_score_keywords_ambigus,
)
from .config import charger_config_emetteurs
from .entry_service import JsonNewEntryDraft, PanDaFiReError


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

    brouillon_nouveau_emetteur = JsonNewEntryDraft(
        config_type="emetteurs",
        description=emetteur_select,
        keywords=generer_keywords_depuis_nom(emetteur_select),
        json_path=emetteur_json_path,
        category=categorie_emetteur,
    )

    try:
        ajouter_nouvelle_entree_json(brouillon_nouveau_emetteur)
    except PanDaFiReError as e:
        typer.echo(f"❌ Échec de l'ajout : {e}")
    else:
        typer.echo(f"✅ '{brouillon_nouveau_emetteur.description}' ajouté !")


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


# def enrich_manuel() -> None:
#     """Enrichir la liste des émetteurs de façon interactive."""

#     emetteurs = charger_config_emetteurs()
#     ecraser = False
#     typer.echo("\n🏢 Ajout d'un nouvel émetteur\n" + "-" * 40)

#     # 1. demander le nom de l'émetteur (obligatoire)
#     nom_nouvel_emetteur = typer.prompt("Nom de l'émetteur").strip()
#     if not nom_nouvel_emetteur:
#         typer.echo("❌ Le nom de la compagnie est obligatoire.")
#         raise typer.Abort()

#     # 2. choisir la catégorie de l'émetteur dans la liste des catégories disponibles
#     categories = list(
#         dict.fromkeys(emetteur["category"] for emetteur in emetteurs.values())
#     )
#     choix_categorie = choisir_dans_liste(
#         categories,
#         titre="Catégories disponibles :",
#         label_prompt=f"Catégorie pour {nom_nouvel_emetteur}",
#     )

#     if choix_categorie is None:
#         typer.echo("❌ La catégorie est obligatoire.")
#         raise typer.Abort()
#     categorie_select = categories[choix_categorie]

#     # 3. vérifier si l'emmeteur existe déjà et demander si le mettre à jour ou annuler
#     if entree_json_existe(nom_nouvel_emetteur, emetteurs):
#         typer.echo(f"⚠️ L'émetteur '{nom_nouvel_emetteur}' existe déjà.")
#         if not typer.confirm("Voulez-vous l'écraser ?", default=False):
#             raise typer.Abort()
#         ecraser = True

#     # 4. demander le restes des informations
#     email = typer.prompt("Email", default="", show_default=False).strip()
#     site_web_a = typer.prompt("Site web", default="", show_default=False).strip()
#     site_web_b = typer.prompt(
#         "Site web alternatif", default="", show_default=False
#     ).strip()
#     telephone = typer.prompt("Téléphone", default="", show_default=False).strip()
#     mot_cle_supplementaire = typer.prompt(
#         "Mots-clés supplémentaires (séparés par des virgules)",
#         default="",
#         show_default=False,
#     ).strip()
#     keywords_emetteur, keywords_ajustes = generer_keywords_emetteur(
#         nom_nouvel_emetteur,
#         email,
#         site_web_a,
#         site_web_b,
#         telephone,
#         mot_cle_supplementaire,
#     )

#     if keywords_ajustes:
#         typer.echo(
#             "⚠️ Certains mots-clés sont ambigus avec d'autres émetteurs connus. Scores ajustés :"
#         )
#         for keyword in keywords_ajustes:
#             typer.echo(
#                 f"   -  mot-clé : '{keyword}' → score ajusté à {keywords_emetteur[keyword]}"
#             )

#     # récap + confirmation
#     typer.echo(f"\n📋 Récapitulatif pour « {nom_nouvel_emetteur} » :")
#     typer.echo(f"Catégorie : {categorie_select}")
#     for mot, poids in keywords_emetteur.items():
#         typer.echo(f"   • {mot} (poids {poids})")

#     if not typer.confirm("\nConfirmer ?", default=True):
#         typer.echo("❌ Annulé.")
#         raise typer.Abort()

#     success = ajouter_nouvelle_entree_json(
#         description=nom_nouvel_emetteur,
#         keywords=keywords_emetteur,
#         json_path=CONFIG_PATH / "emetteurs.json",
#         nom_categorie=categorie_select,
#         overwrite=ecraser,
#     )

    # if success:
    #     typer.echo(
    #         f"✅ {nom_nouvel_emetteur} {'mis à jour' if ecraser else 'ajouté'} !"
    #     )
    # else:
    #     typer.echo("❌ Échec de l'ajout.")
