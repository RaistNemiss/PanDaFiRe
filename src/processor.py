"""Logique de traitement d'un PDF individuel."""

import typer
import shutil
from pathlib import Path

from .extraction import (
    extraire_texte,
    extraire_date_document,
    extraire_candidats_emetteur,
    extraire_noms_societes,
    extraire_nom_pdf_sans_date,
)
from .classifier import identifier_par_score
from .logger import log_decision
from .utils import normaliser_text
from .destinataire import determiner_initiales_destinataire
from .config_path import get_output_path
from .config import trouver_categorie_config


def process_pdf(
    pdf_path: Path,
    types: dict,
    emetteurs: dict,
    destinataires: dict,
    dry_run: bool,
    debug: bool,
    output: bool = False,
) -> None:
    """Traite un fichier PDF : extrait, classifie, renomme."""

    # Extraction + normalisation
    texte_brut, ocr_utilise = extraire_texte(pdf_path)
    texte_normalise = normaliser_text(texte_brut, stopwords=False)  # on garde les stopwords pour la classification émetteur/destinataire

    # Classification
    type_doc, type_doc_scores = identifier_par_score(
        texte_normalise, types, retour_score=True
    )
    nom_emetteur, emetteur_scores = identifier_par_score(
        texte_normalise, emetteurs, retour_score=True
    )
    nom_destinataire = identifier_par_score(texte_normalise, destinataires)

    # Extraction date
    date_doc = extraire_date_document(texte_brut)

    # Fallback émetteur inconnu
    if nom_emetteur == "inconnu":
        candidats_emetteur = extraire_candidats_emetteur(texte_brut)
        candidats_emetteur += extraire_noms_societes(texte_brut)
        nom_emetteur = extraire_nom_pdf_sans_date(pdf_path.stem)
    else:
        candidats_emetteur = []

    # Log
    log_decision(
        pdf_path,
        type_doc,
        type_doc_scores,
        nom_emetteur,
        emetteur_scores,
        candidats_emetteur,
        nom_destinataire,
        date_doc,
        ocr_utilise,
        entete_brut_preview=texte_brut[:200],
        entete_normalise_preview=texte_normalise[:200],
    )

    # Debug
    if debug:
        typer.echo(f"[DEBUG] {pdf_path.name} scores type     : {type_doc_scores}")
        typer.echo(f"[DEBUG] {pdf_path.name} scores émetteur : {emetteur_scores}")

    initiales = determiner_initiales_destinataire(nom_destinataire)
    
    # Dry-run
    if dry_run:
        typer.echo(
            f"[Dry-Run] {pdf_path.name} → "
            f"{type_doc} | {nom_emetteur} | {initiales} | {date_doc}"
        )
        return

    # output
    if output:
        _deplacer_fichier(pdf_path, date_doc, type_doc, nom_emetteur, nom_destinataire, emetteurs)
    else:
        # Renommage
        _renommer_pdf(pdf_path, date_doc, type_doc, nom_emetteur, initiales)


def _construire_nom_pdf(date_doc: str, type_doc: str, nom_emetteur: str, initiales: str | None = None) -> str:
    """Construit un nom de fichier PDF selon la convention de nommage."""
    if initiales is not None:
        return f"{date_doc}_{type_doc}_{nom_emetteur}_{initiales}.pdf"
    return f"{date_doc}_{type_doc}_{nom_emetteur}.pdf"


def _renommer_pdf(pdf_path: Path, date_doc: str, type_doc: str, nom_emetteur: str, initiales: str) -> Path:
    """Renomme le PDF sur place avec les initiales du destinataire."""
    nouveau_nom = _construire_nom_pdf(date_doc, type_doc, nom_emetteur, initiales)
    destination = pdf_path.parent / nouveau_nom

    if destination.exists():
        typer.echo(f"[Skip] Fichier déjà existant : {destination.name}")
        return destination

    pdf_path.rename(destination)
    typer.echo(f"✅ {pdf_path.name} → {destination.name}")
    return destination


def _deplacer_fichier(pdf_path: Path, date_doc: str, type_doc: str, nom_emetteur: str, nom_destinataire: str, emetteurs: dict) -> bool:
    """Déplace le fichier PDF dans le dossier de sortie selon son destinataire et sa catégorie."""
    
    if not pdf_path.exists():
        typer.echo(f"❌ Fichier introuvable : {pdf_path}")
        return False

    if type_doc == "inconnu"or nom_emetteur == "inconnu":
        nom_categorie = "_à_trier"
    else:
        nom_categorie = trouver_categorie_config(nom_emetteur, emetteurs)
    
    #créer le dossier cible
    output_dir = get_output_path() / nom_destinataire / nom_categorie
    output_dir.mkdir(parents=True, exist_ok=True)

    # construire la destination finale
    destination = output_dir / _construire_nom_pdf(date_doc, type_doc, nom_emetteur)
    if destination.exists():
        typer.echo(f"❌ Fichier déjà existant : {destination}")
        return False
  
    shutil.move(str(pdf_path), str(destination)) # shutili.move gère mieux les déplacements entre disques différents que Path.rename
    typer.echo(f"✅ {pdf_path.name} déplacé vers {destination}")
    return True

if __name__ == "__main__":
    pass