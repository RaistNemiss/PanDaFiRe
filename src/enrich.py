from pathlib import Path
from collections import Counter
import re
import typer

from .utils import ajouter_nouvelle_entree_json ,ARTICLES_PREPOSITIONS, enlever_accents, choisir_dans_liste, entree_json_existe
from .config import charger_config_emetteurs



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

def ajouter_emetteur_json(emetteur_select: str, categorie_emetteur: str, emetteur_json_path: Path) -> None:

    nouveau_emetteur = emetteur_select.strip()
    
    emetteur_est_ajoute = ajouter_nouvelle_entree_json(description=nouveau_emetteur, keywords=generer_mot_clef(nouveau_emetteur), json_path=emetteur_json_path, nom_categorie=categorie_emetteur)

    if emetteur_est_ajoute:
        print(f"✅ Émetteur ajouté : {nouveau_emetteur}")       
    else:
        print(f"⚠️ L'émetteur '{nouveau_emetteur}' existe déjà dans la configuration.")


def generer_mot_clef(nom: str) -> dict:

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

def enrich_manuel() -> None:
    """Enrichir la liste des émetteurs de façon interactive."""

    emetteurs = charger_config_emetteurs()

    typer.echo("\n🏢 Ajout d'un nouvel émetteur\n" + "-" * 40)

    # 1. nom de l'émetteur (obligatoire)
    nom_nouvel_emetteur = typer.prompt("Nom de l'émetteur").strip()
    if not nom_nouvel_emetteur:
        typer.echo("❌ Le nom de la compagnie est obligatoire.")
        raise typer.Abort()
    
    # 2. catégorie de l'émetteur choix dans
    categories = list(dict.fromkeys(emetteur["category"] for emetteur in emetteurs.values()))
    choix_categorie = choisir_dans_liste(
        categories,
         titre="Catégories disponibles :",
         label_prompt=f"Catégorie pour {nom_nouvel_emetteur}")
    
    if choix_categorie is None:
        typer.echo("❌ La catégorie est obligatoire.")
        raise typer.Abort()
    categorie_select = categories[choix_categorie]

    if entree_json_existe(nom_nouvel_emetteur, emetteurs):
        typer.echo(f"⚠️ L'émetteur '{nom_nouvel_emetteur}' existe déjà.")
        if not typer.confirm("Voulez-vous l'écraser ?", default=False):
            raise typer.Abort()
        ecraser = True
    
    email = typer.prompt("Email", default="", show_default=False).strip()
    site_web_a = typer.prompt("Site web", default="", show_default=False).strip()
    site_web_b = typer.prompt("Site web alternatif", default="", show_default=False).strip()
    telephone = typer.prompt("Téléphone", default="", show_default=False).strip()
    mot_cle_supplementaire = typer.prompt("Mots-clés supplémentaires (séparés par des virgules)", default="", show_default=False).strip()