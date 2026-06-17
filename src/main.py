"""PanDaFire - A simple automatic PDF rename script by Raist Nemiss."""

import typer
from pathlib import Path
from typing import Callable, Optional

from .destinataire import generer_keywords_destinataire
from .utils import ajouter_nouvelle_entree_json, valider_choix_liste
from .config import (
    charger_config,
    categorie_disponible,
    prepare_nouvelle_entree,
)
from .logger import lire_extraction_log, log_run
from .enrich import (
    generer_keywords_depuis_nom,
    generer_keywords_emetteur,
    candidats_emetteur_a_traiter,
    )
from .processor import process_pdf
from .entry_service import (
    JsonNewEntryDraft,
    PanDaFiReError,
    ValidationError,
    EntryExistsError,
    ProcessResult,
    TypeDeConfig,
    Statut,
)
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
        except PanDaFiReError as e:
            typer.echo(f"❌ Erreur sur {pdf_file.name} : {e}")


def _traiter_fichier(path: Path, dry_run: bool, debug: bool, output: bool) -> None:
    resultat = process_pdf(path, TYPES, EMETTEURS, DESTINATAIRES, dry_run, debug, output)
    _cli_afficher_resultat_run(resultat, debug)


def _cli_afficher_resultat_run(resultat: ProcessResult, debug: bool ) -> None:
    if debug and resultat.scores:
        typer.echo(f"[DEBUG] {resultat.source.name} scores type     : {resultat.scores.get('type')}")
        typer.echo(f"[DEBUG] {resultat.source.name} scores émetteur : {resultat.scores.get('emetteur')}")

    message = {
        Statut.RENOMME: f"✅ {resultat.source.name} → {resultat.destination.name}",
        Statut.DEPLACE: f"✅ {resultat.source.name} déplacé vers",
        Statut.DRY_RUN: f"[Dry-Run] {resultat.source.name} → {resultat.destination.name}",
        }
    typer.echo(message[resultat.statut])

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
        _cli_ajouter_nouvelle_entree_json(
            json_path=CONFIG_PATH / "emetteurs.json", type_de_config="emetteurs"
        )
        return

    # Fonction locale pour formater un candidat (nom, occurrence)
    def format_candidat(c) -> str:
        return f"{c[0]} : {c[1]} occurrence(s)"

    while True:
        # recharger la config à chaque tour pour refléter les ajouts précédents,
        candidats, categories = candidats_emetteur_a_traiter(lire_extraction_log())

        if not candidats:
            typer.echo("Aucun nouveau candidat à traiter. 🎉")
            return

        # Étape 1 : choisir le candidat
        choix_candidat_emetteur = _choisir_dans_liste(
            candidats,
            titre="Candidats émetteurs fréquents :",
            label_prompt="Choisir un candidat",
            formatter=format_candidat,
        )
        if choix_candidat_emetteur is None:
            return
        nom_candidat = candidats[choix_candidat_emetteur][0]

        # Étape 2 : choisir la catégorie
        choix_categorie = _choisir_dans_liste(
            categories,
            titre="Catégories disponibles :",
            label_prompt=f"Catégorie pour '{nom_candidat}'",
        )
        if choix_categorie is None:
            return
        categorie_select = categories[choix_categorie]


        # Étape 3 : construction du brouillon (mécanique pure, GUI-ready)
        brouillon = JsonNewEntryDraft(
            config_type="emetteurs",
            description=nom_candidat,
            keywords=generer_keywords_depuis_nom(nom_candidat),
            json_path=CONFIG_PATH / "emetteurs.json",
            category=categorie_select,
        )

        try:
            prepare_nouvelle_entree(brouillon)
        except ValidationError as e:
            typer.echo(f"❌ {e}")
            continue  # revenir à la liste des candidats
        except EntryExistsError as e:
            typer.echo(f"⚠️ {e}")
            if not typer.confirm("Voulez-vous l'écraser ?", default=False):
                continue  # revenir à la liste des candidats
            brouillon.overwrite = True

        try:
            ajouter_nouvelle_entree_json(brouillon)
        except PanDaFiReError as e:
            typer.echo(f"❌ Échec de l'ajout : {e}")
            continue  # revenir à la liste des candidats
        else:
            typer.echo(f"✅ '{nom_candidat}' ajouté dans '{categorie_select}'")


@app.command()
@log_run
def register(json_path: Path = CONFIG_PATH / "destinataire.json") -> None:
    """Ajoute un nouveau destinataire de façon interactive."""
    _cli_ajouter_nouvelle_entree_json(
        json_path=json_path, type_de_config="destinataires"
    )


def _cli_ajouter_nouvelle_entree_json(
    json_path: Path, type_de_config: TypeDeConfig
) -> None:
    """Ajoute une nouvelle entree dans un fichier config_json de façon interactive."""

    nom_complet, prenom, nom = _cli_saisir_identite(type_de_config)

    brouillon = JsonNewEntryDraft(
        type_de_config, nom_complet, keywords={}, json_path=json_path
    )

    # 1. Validation brouillon + vérification existence dans JSON destinataires
    try:
        prepare_nouvelle_entree(brouillon)
    except ValidationError as e:
        typer.echo(f"❌ {e}")
        raise typer.Abort()
    except EntryExistsError as e:
        typer.echo(f"⚠️ {e}")
        if not typer.confirm("Voulez-vous l'écraser ?", default=False):
            raise typer.Abort()
        brouillon.overwrite = True

    # 2. Saisie des mots-clé avec score d'importance
    _cli_saisir_mots_cles(brouillon, type_de_config, prenom, nom)

    # 3. Récapitulatif + confirmation
    _afficher_recap_confirmer(brouillon)

    # 4. Ajout dans le JSON
    try:
        ajouter_nouvelle_entree_json(brouillon)
    except PanDaFiReError as e:
        typer.echo(f"❌ Échec de l'ajout : {e}")
        raise typer.Abort()
    else:
        typer.echo(
            f"✅ '{nom_complet}' {'mis à jour' if brouillon.overwrite else 'ajouté'} !"
        )


def _cli_saisir_identite(type_de_config: TypeDeConfig) -> tuple[str, str, str]:

    # Séquence guidée
    if type_de_config == "destinataires":
        typer.echo("\n📇 Ajout d'un nouveau destinataire\n" + "-" * 40)
        prenom = typer.prompt("Prénom").strip()
        nom = typer.prompt("Nom").strip()
        nom_complet = f"{prenom} {nom}".strip()
        return nom_complet, prenom, nom

    if type_de_config == "emetteurs":
        typer.echo("\n📇 Ajout d'un nouvel émetteur\n" + "-" * 40)
        nom_complet = typer.prompt("Nom de l'émetteur").strip()
        return nom_complet, "", ""

    raise ValidationError(f"Type de config non géré : {type_de_config}")


def _cli_saisir_mots_cles(
    brouillon: JsonNewEntryDraft, type_de_config: TypeDeConfig, prenom: str, nom: str
) -> None:
    """Guide l'utilisateur pour saisir les mots-clé et leurs poids d'importance."""

    email = typer.prompt("Email", default="", show_default=False).strip()
    telephone = typer.prompt("Téléphone", default="", show_default=False).strip()

    # Destinataires
    if type_de_config == "destinataires":
        brouillon.keywords = generer_keywords_destinataire(
            nom, prenom, email, telephone
        )

    # Emetteurs
    if type_de_config == "emetteurs":
        # site web et mots-clé supplémentaires pour les émetteurs
        site_web_a = typer.prompt("Site web", default="", show_default=False).strip()
        site_web_b = typer.prompt(
            "Site web alternatif", default="", show_default=False
        ).strip()
        mot_cle_supplementaire = typer.prompt(
            "Mots-clés supplémentaires (séparés par des virgules)",
            default="",
            show_default=False,
        ).strip()

        brouillon.keywords, brouillon.keywords_ajustes = generer_keywords_emetteur(
            brouillon.description,
            email,
            site_web_a,
            site_web_b,
            telephone,
            mot_cle_supplementaire,
        )

        categories = categorie_disponible(type_de_config=type_de_config)
        choix_categorie = _choisir_dans_liste(
            items=categories,
            titre="Catégories disponibles :",
            label_prompt=f"Catégorie pour {brouillon.description}",
        )
        if choix_categorie is None:
            raise typer.Abort()
        brouillon.category = categories[choix_categorie]


def _afficher_recap_confirmer(nouvelle_entree_brouillon: JsonNewEntryDraft):
    """
    Affiche le récapitulatif d'un draft et demande confirmation à l'utilisateur.

    Lève typer.Abort() si l'utilisateur refuse.
    """

    typer.echo(f"\n📋 Récapitulatif pour « {nouvelle_entree_brouillon.description} » :")

    # 1. afficher catégorie si présente
    if nouvelle_entree_brouillon.category:
        typer.echo(f"   📂 Catégorie : {nouvelle_entree_brouillon.category}")

    # 2. afficher les mots clé et leurs poids
    typer.echo("   🔑 Keywords :")
    for mot, poids in nouvelle_entree_brouillon.keywords.items():
        typer.echo(f"      • {mot} (poids {poids})")

    # 3. avertissment mots ajustés
    if nouvelle_entree_brouillon.keywords_ajustes:
        typer.echo(
            f"\n les mots clés suivant ont vu leur poids réduits cars ils sont partagés d'autres {nouvelle_entree_brouillon.config_type}."
        )
        for mot in nouvelle_entree_brouillon.keywords_ajustes:
            typer.echo(f"      • {mot}")

    # 4. avertissment écrasement
    if nouvelle_entree_brouillon.overwrite:
        typer.echo(
            f"\n   🔄 ATTENTION : l'entrée « {nouvelle_entree_brouillon.description} » "
            "existe déjà et sera écrasée."
        )

    # 5. confirmation
    if not typer.confirm("\nConfirmer ?", default=True):
        typer.echo("❌ Annulé.")
        raise typer.Abort()


def _choisir_dans_liste(
    items: list,
    titre: str,
    label_prompt: str,
    formatter: Callable[[str], str] = str,
) -> Optional[int]:
    """
    Affiche une liste numérotée et demande à l'utilisateur d'en choisir un élément.

    Retourne l'index choisi (0-based) ou None si annulé/invalide.
    """
    typer.echo(f"\n📋 {titre}")
    for i, item in enumerate(items, start=1):
        typer.echo(f"  {i} - {formatter(item)}")

    choix = typer.prompt(f"{label_prompt} (0 pour quitter)", type=int)


    index = valider_choix_liste(choix, len(items))
    if index is None:
        typer.echo("❌ Annulé ou choix invalide.")
        return None
    
    if not typer.confirm(f"Confirmer : {formatter(items[index])} ?", default=True):
        typer.echo("❌ Annulé.")
        return None
    return index


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
