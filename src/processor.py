"""Logique de traitement d'un PDF individuel."""

import shutil
from pathlib import Path

from .extraction import (
    extraire_texte,
    extraire_date_document,
    extraire_candidats_emetteur,
    extraire_noms_societes,
    extraire_nom_pdf_sans_date,
)
from .entry_service import (
    ProcessPdfResult,
    Statut,
    FileAlreadyExistError,
    FileNotFoundError,
)
from .classifier import identifier_par_score
from .logger import extraction_logger
from .utils import normaliser_text
from .destinataire import determiner_initiales_destinataire
from .config_path import get_output_path
from .config import trouver_categorie_config


def process_pdf(
    pdf_path: Path,
    types: dict,
    emetteurs: dict,
    destinataire: dict,
    dry_run: bool,
    debug: bool,
    output: bool = False,
) -> ProcessPdfResult:
    """Traite un fichier PDF : extrait, classifie, renomme."""

    # 1. Extraction + normalisation
    texte_brut, ocr_utilise = extraire_texte(pdf_path)
    texte_normalise = normaliser_text(
        texte_brut, stopwords=False
    )  # on garde les stopwords pour la classification émetteur/destinataire

    # 2. Classification
    type_doc, type_doc_scores = identifier_par_score(
        texte_normalise, types, retour_score=True
    )
    nom_emetteur, emetteur_scores = identifier_par_score(
        texte_normalise, emetteurs, retour_score=True
    )
    nom_destinataire = identifier_par_score(texte_normalise, destinataire)

    # 3. Extraction date
    date_doc = extraire_date_document(texte_brut)

    # 4. Fallback émetteur inconnu
    if nom_emetteur == "inconnu":
        candidats_emetteur = extraire_candidats_emetteur(texte_brut)
        candidats_emetteur += extraire_noms_societes(texte_brut)
        nom_emetteur = extraire_nom_pdf_sans_date(pdf_path.stem)
    else:
        candidats_emetteur = []

    # 5. Log
    extraction_logger(
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

    initiales = determiner_initiales_destinataire(nom_destinataire)
    scores = {"type": type_doc_scores, "emetteur": emetteur_scores} if debug else {}

    # Dry-run
    if dry_run:
        return ProcessPdfResult(
            source=pdf_path,
            statut=Statut.DRY_RUN,
            destination=Path(
                _construire_nom_pdf(date_doc, type_doc, nom_emetteur, initiales)
            ),
            scores=scores,
        )

    # Deplacement fichier
    if output:
        return _deplacer_fichier(
            pdf_path,
            date_doc,
            type_doc,
            nom_emetteur,
            nom_destinataire,
            emetteurs,
            scores,
        )

    return _renommer_pdf(pdf_path, date_doc, type_doc, nom_emetteur, initiales, scores)


def _construire_nom_pdf(
    date_doc: str, type_doc: str, nom_emetteur: str, initiales: str | None = None
) -> str:
    """Construit un nom de fichier PDF selon la convention de nommage."""
    if initiales is not None:
        return f"{date_doc}_{type_doc}_{nom_emetteur}_{initiales}.pdf"
    return f"{date_doc}_{type_doc}_{nom_emetteur}.pdf"


def _renommer_pdf(
    pdf_path: Path,
    date_doc: str,
    type_doc: str,
    nom_emetteur: str,
    initiales: str,
    scores: dict,
) -> ProcessPdfResult:
    """Renomme le PDF sur place avec les initiales du destinataire."""
    nouveau_nom = _construire_nom_pdf(date_doc, type_doc, nom_emetteur, initiales)
    destination = pdf_path.parent / nouveau_nom

    # le fichier existe déjà à la destination
    if destination.exists():
        raise FileAlreadyExistError(destination)

    pdf_path.rename(destination)
    return ProcessPdfResult(pdf_path, Statut.RENOMME, destination, scores)


def _deplacer_fichier(
    pdf_path: Path,
    date_doc: str,
    type_doc: str,
    nom_emetteur: str,
    nom_destinataire: str,
    emetteurs: dict,
    scores: dict,
) -> ProcessPdfResult:
    """Déplace le fichier PDF dans le dossier de sortie selon son destinataire et sa catégorie."""

    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)

    if type_doc == "inconnu" or nom_emetteur == "inconnu":
        nom_categorie = "_à_trier"
    else:
        nom_categorie = trouver_categorie_config(nom_emetteur, emetteurs)

    # créer le dossier cible
    output_dir = get_output_path() / nom_destinataire / nom_categorie
    output_dir.mkdir(parents=True, exist_ok=True)

    # construire la destination finale
    destination = output_dir / _construire_nom_pdf(date_doc, type_doc, nom_emetteur)
    if destination.exists():
        raise FileAlreadyExistError(destination)

    shutil.move(
        str(pdf_path), str(destination)
    )  # shutil.move gère mieux les déplacements entre disques différents que Path.rename
    return ProcessPdfResult(pdf_path, Statut.DEPLACE, destination, scores)


if __name__ == "__main__":
    pass
