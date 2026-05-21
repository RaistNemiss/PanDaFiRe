"""PanDaFire - A simple automatic PDF rename script by Raist Nemiss."""

import typer
import json
from pathlib import Path

from .extraction import (
    extraire_texte,
    extraire_date_document,
    extraire_candidats_emetteur,
    extraire_noms_societes,
    extraire_nom_pdf_sans_date
)
from .classifier import identifier_par_score
from .logger import log_decision, lire_log
from .enrich import candidats_frequents, ajouter_emetteur_json
from .utils import normaliser_text
from .config_path import CONFIG_PATH, DESTINATAIRE_PATH, TYPES_PATH, EMETTEURS_PATH
from .destinataire import chargement_destinataires
app = typer.Typer()


with open(TYPES_PATH, encoding="utf-8") as f:
    TYPES = json.load(f)

with open(EMETTEURS_PATH, encoding="utf-8") as f:
    EMETTEURS = json.load(f)

DESTINATAIRES = chargement_destinataires(DESTINATAIRE_PATH)

def process_pdf(pdf_path: Path, dry_run: bool, debug: bool) -> None:
    
    # Extraction du texte du PDF (avec OCR si nécessaire)
    texte_brut, ocr_utilise = extraire_texte(pdf_path)

    # Normalisation du texte pour améliorer la classification (ex: suppression des accents, mise en minuscule, suppression des espaces superflus)
    texte_normalise = normaliser_text(texte_brut)

    # classifcation du text normalisé
    type_doc, type_doc_scores = identifier_par_score(texte_normalise, TYPES, retour_score=True)
    emetteur, emetteur_scores = identifier_par_score(texte_normalise, EMETTEURS, retour_score=True)
    destinataire = identifier_par_score(texte_normalise, DESTINATAIRES,)

    # extraction de la date du document à partir du texte normalisé (plus fiable que le texte brut pour éviter les faux positifs liés à l'OCR)
    date_doc = extraire_date_document(texte_normalise)

    if emetteur == "inconnu":
        candidats_emetteur = extraire_candidats_emetteur(texte_brut)
        candidats_emetteur += extraire_noms_societes(texte_brut)
        emetteur = extraire_nom_pdf_sans_date(pdf_path.stem)
    else:
        candidats_emetteur = []

    log_decision(
        pdf_path,
        type_doc,
        type_doc_scores,
        emetteur,
        emetteur_scores,
        candidats_emetteur,
        destinataire, 
        date_doc,
        ocr_utilise,
        entete_brut_preview=texte_brut[:200],  # on limite à 200 caractères pour éviter les logs trop lourds
        entete_normalise_preview=texte_normalise[:200],  # on limite à 200 caractères pour éviter les logs trop lourds
    )

    if debug:
        typer.echo(f"[DEBUG] {pdf_path.name} scores type: {type_doc_scores}")
        typer.echo(f"[DEBUG] {pdf_path.name} scores émetteur: {emetteur_scores}")

    if dry_run:
        typer.echo(
            f"[Dry-Run] Le document {pdf_path.name} est identifié comme : {type_doc} - Émetteur : {emetteur} - Date : {date_doc}"
        )
        return

    nouveau_nom_pdf = Path(f"{date_doc}_{type_doc}_{emetteur}.pdf")
    destination = pdf_path.parent / nouveau_nom_pdf

    if destination.exists():
        typer.echo(f"[Skip] Le fichier existe déjà : {destination.name}")
        return

    pdf_path.rename(destination)
    typer.echo(f"Le PDF {pdf_path.name} a été renommé en : {destination.name}")

@app.command()
def run(
    path: Path = typer.Argument(
        ..., help="Chemin vers le fichier PDF ou le dossier à traiter"
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        "-d",
        help="Afficher les scores de classification pour le type de document et l'émetteur",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-n",
        help="Afficher le nouveau nom sans renommer le fichier",
    ),
    recursive: bool = typer.Option(
        False,
        "--recursive",
        "-r",
        help="Traiter aussi les sous-dossiers si le chemin donné est un dossier",
    ),
):
    if path.is_dir():
        pdf_files = sorted(path.rglob("*.pdf")) if recursive else sorted(path.glob("*.pdf"))
        if not pdf_files:
            typer.echo(f"Aucun fichier PDF trouvé dans le dossier : {path}")
            raise typer.Exit(code=1)

        typer.echo(f"Traitement de {len(pdf_files)} fichier(s) dans le dossier : {path}")
        for pdf_file in pdf_files:
            process_pdf(pdf_file, dry_run=dry_run, debug=debug)
        return

    if path.is_file():
        process_pdf(path, dry_run=dry_run, debug=debug)
        return

    typer.echo(f"Le chemin spécifié n'existe pas : {path}")
    raise typer.Exit(code=1)


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

    typer.confirm(f"Vous avez choisi : {candidats[choix - 1][0] if choix > 0 else 'Aucun candidat'}", abort=True)

    candidat_select = candidats[choix - 1]
    typer.echo(f"Candidat sélectionné : {candidat_select}")
    typer.echo(25 * "-")
    for i, (categorie) in enumerate(categorie_emetteurs, start=1):
        typer.echo(f"{i} - {categorie}")

    choix = typer.prompt(
        f"Choisir une catégorie pour le candidat : {candidat_select[0]} (0 pour quitter)",
        type=int,
    )

    typer.confirm(f"Vous avez choisi : {categorie_emetteurs[choix - 1] if choix > 0 else 'Aucune catégorie'}", abort=True)

    if choix == 0:
        typer.echo("Aucune catégorie sélectionnée.")
        return

    emetteur_select = categorie_emetteurs[choix - 1]
    ajouter_emetteur_json(candidat_select[0], emetteur_select, CONFIG_PATH / "emetteurs.json")


if __name__ == "__main__":
    app()
