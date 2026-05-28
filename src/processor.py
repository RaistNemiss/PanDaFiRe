"""Logique de traitement d'un PDF individuel."""

import typer
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
from .config_path import OUTPUT_PATH
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
    texte_normalise = normaliser_text(texte_brut)

    # Classification
    type_doc, type_doc_scores = identifier_par_score(
        texte_normalise, types, retour_score=True
    )
    emetteur, emetteur_scores = identifier_par_score(
        texte_normalise, emetteurs, retour_score=True
    )
    nom_destinataire = identifier_par_score(texte_normalise, destinataires)

    # Extraction date
    date_doc = extraire_date_document(texte_brut)

    # Fallback émetteur inconnu
    if emetteur == "inconnu":
        candidats_emetteur = extraire_candidats_emetteur(texte_brut)
        candidats_emetteur += extraire_noms_societes(texte_brut)
        emetteur = extraire_nom_pdf_sans_date(pdf_path.stem)
    else:
        candidats_emetteur = []

    # Log
    log_decision(
        pdf_path,
        type_doc,
        type_doc_scores,
        emetteur,
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

    # Dry-run
    if dry_run:
        initiales = determiner_initiales_destinataire(nom_destinataire)
        typer.echo(
            f"[Dry-Run] {pdf_path.name} → "
            f"{type_doc} | {emetteur} | {initiales} | {date_doc}"
        )
        return

    # output
    if output:
        _déplacer_fichier(pdf_path, date_doc, type_doc, emetteur, nom_destinataire)
        return

    # Renommage
    _renommer_pdf(pdf_path, date_doc, type_doc, emetteur)

def _renommer_pdf(
    pdf_path: Path,
    date_doc: str,
    type_doc: str,
    emetteur: str,
) -> Path:
    """Renomme le fichier PDF selon la convention de nommage."""
    nouveau_nom = Path(f"{date_doc}_{type_doc}_{emetteur}.pdf")
    destination = pdf_path.parent / nouveau_nom

    if destination.exists():
        typer.echo(f"[Skip] Fichier déjà existant : {destination.name}")
        return destination

    pdf_path.rename(destination)
    typer.echo(f"✅ {pdf_path.name} → {destination.name}")
    return destination

def _déplacer_fichier(pdf_path: Path, date_doc: str, type_doc: str, emetteur: str, nom_destinataire: str) -> bool:
    """Déplace le fichier PDF dans le dossier de sortie selon son destinataire et sa catégorie."""

    if type_doc == "inconnu":
        nom_categorie = "catégorie_non_triée"
    else:
        nom_categorie = trouver_categorie_config(emetteur)
        
    # vérifier si le dossier de sortie existe
    output_dir = OUTPUT_PATH / nom_destinataire / nom_categorie
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
        typer.echo(f"📁 Dossier créé : {output_dir}")
    
    nouveau_nom_pdf = _renommer_pdf(pdf_path, date_doc, type_doc, emetteur).name

    if pdf_path.exists():
        destination = output_dir / nouveau_nom_pdf
        if destination.exists():
            typer.echo(f"[Skip] Fichier déjà existant : {destination.name}")
            return False
        pdf_path.rename(destination)
        typer.echo(f"✅ {pdf_path.name} déplacé vers {destination}")
        return True
    else:
        typer.echo(f"❌ Fichier introuvable : {pdf_path}")
        return False


if __name__ == "__main__":
    _déplacer_fichier(Path(r"C:\Users\afarina\Downloads\w61477151.pdf"), "2024-01-01", "Facture", "Emetteur", "AB")