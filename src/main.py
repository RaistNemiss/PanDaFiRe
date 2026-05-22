"""PanDaFire - A simple automatic PDF rename script by Raist Nemiss."""

import typer
from pathlib import Path

from .config import charger_config
from .processor import process_pdf
from .logger import lire_log
from .enrich import candidats_frequents, ajouter_emetteur_json
from .config_path import CONFIG_PATH

app = typer.Typer()

# Chargement unique au démarrage
TYPES, EMETTEURS, DESTINATAIRES = charger_config()


@app.command()
def run(
    path: Path = typer.Argument(..., help="Fichier PDF ou dossier à traiter"),
    debug: bool = typer.Option(False, "--debug", "-d", help="Afficher les scores"),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Simuler sans renommer"),
    recursive: bool = typer.Option(False, "--recursive", "-r", help="Inclure les sous-dossiers"),
):
    if path.is_dir():
        _traiter_dossier(path, recursive, dry_run, debug)
    elif path.is_file():
        _traiter_fichier(path, dry_run, debug)
    else:
        typer.echo(f"❌ Chemin introuvable : {path}")
        raise typer.Exit(code=1)


def _traiter_dossier(path: Path, recursive: bool, dry_run: bool, debug: bool) -> None:
    pdf_files = sorted(path.rglob("*.pdf") if recursive else path.glob("*.pdf"))

    if not pdf_files:
        typer.echo(f"Aucun PDF trouvé dans : {path}")
        raise typer.Exit(code=1)

    typer.echo(f"📂 {len(pdf_files)} fichier(s) trouvé(s) dans : {path}")
    for pdf_file in pdf_files:
        try:
            _traiter_fichier(pdf_file, dry_run, debug)
        except Exception as e:
            typer.echo(f"❌ Erreur sur {pdf_file.name} : {e}")


def _traiter_fichier(path: Path, dry_run: bool, debug: bool) -> None:
    process_pdf(path, TYPES, EMETTEURS, DESTINATAIRES, dry_run, debug)


@app.command()
def enrich():
    """Enrichir la liste des émetteurs depuis les candidats fréquents."""
    candidats = candidats_frequents(lire_log())

    categories = list(dict.fromkeys(
        emetteur["category"] for emetteur in EMETTEURS.values()
    ))

    typer.echo("📋 Candidats émetteurs fréquents :")
    for i, (nom, occurrence) in enumerate(candidats, start=1):
        typer.echo(f"  {i} - {nom} : {occurrence} occurrence(s)")

    choix = typer.prompt("Choisir un candidat (0 pour quitter)", type=int)
    if choix == 0:
        typer.echo("Annulé.")
        return

    candidat_select = candidats[choix - 1]
    typer.confirm(f"Confirmer : {candidat_select[0]} ?", abort=True)

    typer.echo("\n📋 Catégories disponibles :")
    for i, cat in enumerate(categories, start=1):
        typer.echo(f"  {i} - {cat}")

    choix_cat = typer.prompt(
        f"Catégorie pour '{candidat_select[0]}' (0 pour quitter)", type=int
    )
    if choix_cat == 0:
        typer.echo("Annulé.")
        return

    categorie_select = categories[choix_cat - 1]
    typer.confirm(f"Confirmer la catégorie : {categorie_select} ?", abort=True)

    ajouter_emetteur_json(candidat_select[0], categorie_select, CONFIG_PATH / "emetteurs.json")
    typer.echo(f"✅ '{candidat_select[0]}' ajouté dans '{categorie_select}'")


if __name__ == "__main__":
    app()
    