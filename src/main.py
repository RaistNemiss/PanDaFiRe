"""PanDaFire - A simple automatic PDF rename script by Raist Nemiss."""

import typer
import json
from pathlib import Path

from .extraction import (
    extraire_texte,
    extraire_date_document,
    extraire_candidats_emetteur,
    extraire_noms_societes,
)
from .classifier import identifier_par_score
from .logger import log_decision, lire_log
from .enrich import candidats_frequents, ajouter_emetteur_json

app = typer.Typer()


CONFIG_PATH = Path("config")

with open(CONFIG_PATH / "types_documents.json", encoding="utf-8") as f:
    TYPES = json.load(f)

with open(CONFIG_PATH / "emetteurs.json", encoding="utf-8") as f:
    EMETTEURS = json.load(f)


@app.command()
def run(
    pdf_path: Path = typer.Argument(..., help="Chemin vers le fichier PDF à traiter"),
    debug: bool = typer.Option(
        False,
        "--debug",
        "-d",
        help="Afficher les scores de classification pour le type de document et l'émetteur",
    ),
    dry_run: bool = typer.Option(
        True, "--dry-run", "-n", help="Afficher le nouveau nom sans renommer le fichier"
    ),
):

    texte, ocr_utilise = extraire_texte(pdf_path)

    type_doc, type_doc_scores = identifier_par_score(texte, TYPES, retour_score=True)
    date_doc = extraire_date_document(texte)
    emetteur, emetteur_scores = identifier_par_score(
        texte, EMETTEURS, retour_score=True
    )

    if (
        emetteur == "inconnu"
    ):  # si l'émetteur n'est pas identifié avec suffisamment de confiance, on extrait des candidats potentiels pour analyse manuelle
        candidats_emetteur = extraire_candidats_emetteur(texte)
        candidats_emetteur += extraire_noms_societes(texte)
    else:
        candidats_emetteur = []

    log_decision(
        pdf_path,
        type_doc,
        type_doc_scores,
        emetteur,
        emetteur_scores,
        candidats_emetteur,
        date_doc,
        ocr_utilise,
    )

    print(
        f"Le document {pdf_path.name} est identifié comme : {type_doc} - Emetteur du document : {emetteur} - Date extraite : {date_doc}"
    )


@app.command()
def enrich():
    candidats = candidats_frequents(lire_log())

    # Récupère la liste des catégories uniques (sans doublons)
    categories = [emetteur["category"] for emetteur in EMETTEURS.values()]
    categorie_emetteurs = list(dict.fromkeys(categories))

    typer.echo("Candidats émetteurs fréquents :")
    for i, (nom, occurrence) in enumerate(candidats, start=1):
        typer.echo(f"{i}  - {nom} : {occurrence} occurrences")

    choix = typer.prompt("Choisir un candidat (0 pour quitter)", type=int)

    if choix == 0:
        typer.echo("Aucun candidat sélectionné.")
        return

    candidat_select = candidats[choix - 1]
    typer.echo(f"Candidat sélectionné : {candidat_select}")
    typer.echo(25 * "-")
    for i, (categorie) in enumerate(categorie_emetteurs, start=1):
        typer.echo(f"{i} - {categorie}")

    choix = typer.prompt(
        f"Choisir une catégorie pour le candidat : {candidat_select[0]} (0 pour quitter)",
        type=int,
    )

    if choix == 0:
        typer.echo("Aucune catégorie sélectionnée.")
        return

    emetteur_select = categorie_emetteurs[choix - 1]
    ajouter_emetteur_json(candidat_select[0], emetteur_select, CONFIG_PATH / "emetteurs.json")


if __name__ == "__main__":
    app()
