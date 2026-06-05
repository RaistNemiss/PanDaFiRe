"""PanDaFire - A simple automatic PDF rename script by Raist Nemiss."""

import typer
from pathlib import Path

from .destinataire import generer_keywords_destinataire, destinataire_existe
from .utils import ajouter_nouvelle_entree_json, choisir_dans_liste
from .config import charger_config, charger_config_emetteurs
from .processor import process_pdf
from .logger import lire_extraction_log, log_run
from .enrich import candidats_frequents, ajouter_emetteur_json, enrich_manuel
from .config_path import (
    CONFIG_PATH,
    DEFAULT_OUTPUT_PATH,
    set_output_path,
    get_output_path,
)

app = typer.Typer()

# Chargement unique au démarrage
TYPES, EMETTEURS, DESTINATAIRES = charger_config()


@app.command()
@log_run
def run(
    path: Path = typer.Argument(..., help="Fichier PDF ou dossier à traiter"),
    debug: bool = typer.Option(False, "--debug", "-d", help="Afficher les scores"),
    dry_run: bool = typer.Option(
        False, "--dry-run", "-n", help="Simuler sans renommer"
    ),
    recursive: bool = typer.Option(
        False, "--recursive", "-r", help="Inclure les sous-dossiers"
    ),
    output: bool = typer.Option(
        False,
        "--output",
        "-o",
        help=f"Autoriser le déplacement des fichiers renommés dans le dossier de sortie (par défaut : {DEFAULT_OUTPUT_PATH})",
    ),
):
    """Traite un fichier PDF ou tous les PDF d'un dossier."""
    if path.is_dir():
        _traiter_dossier(path, recursive, dry_run, debug, output)
    elif path.is_file():
        _traiter_fichier(path, dry_run, debug, output)
    else:
        typer.echo(f"❌ Chemin introuvable : {path}")
        raise typer.Exit(code=1)


def _traiter_dossier(
    path: Path, recursive: bool, dry_run: bool, debug: bool, output: bool
) -> None:
    pdf_files = sorted(path.rglob("*.pdf") if recursive else path.glob("*.pdf"))

    if not pdf_files:
        typer.echo(f"Aucun PDF trouvé dans : {path}")
        raise typer.Exit(code=1)

    typer.echo(f"📂 {len(pdf_files)} fichier(s) trouvé(s) dans : {path}")
    for pdf_file in pdf_files:
        try:
            _traiter_fichier(pdf_file, dry_run, debug, output)
        except Exception as e:
            typer.echo(f"❌ Erreur sur {pdf_file.name} : {e}")


def _traiter_fichier(path: Path, dry_run: bool, debug: bool, output: bool) -> None:
    process_pdf(path, TYPES, EMETTEURS, DESTINATAIRES, dry_run, debug, output)


@app.command()
@log_run
def enrich(
    manual: bool = typer.Option(
        False,
        "--manual",
        "-m",
        help="Ajouter manuellement un émetteur sans passer par les candidats fréquents",
    ),
) -> None:
    """Enrichir la liste des émetteurs depuis les candidats fréquents."""

    if manual:
        enrich_manuel()

    # Fonction locale pour formater un candidat (nom, occurrence)
    def format_candidat(c) -> str:
        return f"{c[0]} : {c[1]} occurrence(s)"

    while True:
        # recharger la config à chaque tour pour refléter les ajouts précédents,
        emetteurs = charger_config_emetteurs()
        candidats = candidats_frequents(lire_extraction_log())
        emetteurs_connus = set()
        for emetteur in emetteurs.values():
            emetteurs_connus.add(emetteur["description"].lower())
            emetteurs_connus.update(
                keyword.lower() for keyword in emetteur.get("keywords", {})
            )
        categories = list(
            dict.fromkeys(emetteur["category"] for emetteur in emetteurs.values())
        )

        # filtrer les candidats déjà connus dans les émetteurs
        candidats = [c for c in candidats if c[0].lower() not in emetteurs_connus]

        if not candidats:
            typer.echo("Aucun nouveau candidat à traiter. 🎉")
            return

        # Étape 1 : choisir le candidat
        choix_candidat_emetteur = choisir_dans_liste(
            candidats,
            titre="Candidats émetteurs fréquents :",
            label_prompt="Choisir un candidat",
            formatter=format_candidat,
        )
        if choix_candidat_emetteur is None:
            return
        nom_candidat = candidats[choix_candidat_emetteur][0]

        # Étape 2 : choisir la catégorie
        choix_categorie = choisir_dans_liste(
            categories,
            titre="Catégories disponibles :",
            label_prompt=f"Catégorie pour '{nom_candidat}'",
        )
        if choix_categorie is None:
            return
        categorie_select = categories[choix_categorie]

        # Étape 3 : ajout dans le fichier JSON des émetteurs
        ajouter_emetteur_json(
            nom_candidat, categorie_select, CONFIG_PATH / "emetteurs.json"
        )
        typer.echo(f"✅ '{nom_candidat}' ajouté dans '{categorie_select}'")

        if not typer.confirm("Ajouter un autre émetteur ?"):
            break


@app.command()
@log_run
def register(json_path: Path = CONFIG_PATH / "destinataire.json") -> None:
    """Ajoute un nouveau destinataire de façon interactive."""

    typer.echo("\n📇 Ajout d'un nouveau destinataire\n" + "-" * 40)

    # Séquence guidée
    prenom = typer.prompt("Prénom").strip()
    nom = typer.prompt("Nom").strip()
    nom_complet = f"{prenom} {nom}".strip()
    ecraser = False

    # obliger au moins un prénom ou un nom pour éviter les entrées génériques "inconnu".
    if not prenom and not nom:
        typer.echo("❌ Au moins un prénom ou un nom doit être fourni.")
        raise typer.Abort()

    # Vérification de l'existence du destinataire dans le JSON Destinataires
    if destinataire_existe(nom_complet):
        typer.echo(f"⚠️ Le destinataire '{nom_complet}' existe déjà.")
        if not typer.confirm("Voulez-vous l'écraser ?", default=False):
            raise typer.Abort()
        ecraser = True

    email = typer.prompt("Email", default="", show_default=False).strip()
    telephone = typer.prompt("Téléphone", default="", show_default=False).strip()

    keywords_destinataire = generer_keywords_destinataire(nom, prenom, email, telephone)

    # Récap + confirmation
    typer.echo(f"\n📋 Récapitulatif pour « {nom_complet} » :")
    for mot, poids in keywords_destinataire.items():
        typer.echo(f"   • {mot} (poids {poids})")

    if not typer.confirm("\nConfirmer ?", default=True):
        typer.echo("❌ Annulé.")
        raise typer.Abort()

    success = ajouter_nouvelle_entree_json(
        description=nom_complet,
        keywords=keywords_destinataire,
        json_path=json_path,
        overwrite=ecraser,
    )
    if success:
        typer.echo(f"✅ {nom_complet} {'mis à jour' if ecraser else 'ajouté'} !")
    else:
        typer.echo("❌ Échec de l'ajout.")


@app.command()
@log_run
def set_output(
    nouveau_output_path: Path = typer.Argument(
        ...,
        help=f"Configurer le dossier de sortie pour les fichiers renommés (actuellement : {get_output_path()})",
    ),
) -> None:
    """Définir le dossier de sortie pour les fichiers renommés."""
    if not nouveau_output_path.is_dir():
        typer.echo(
            f"❌ Le chemin spécifié n'est pas un dossier : {nouveau_output_path}"
        )
        raise typer.Exit(code=1)

    set_output_path(nouveau_output_path)
    typer.echo(f"✅ Dossier de sortie défini : {nouveau_output_path.resolve()}")


if __name__ == "__main__":
    app()
