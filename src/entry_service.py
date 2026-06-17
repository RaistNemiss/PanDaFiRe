from pathlib import Path
from dataclasses import dataclass, field
from typing import Literal
from enum import Enum


TypeDeConfig = Literal["emetteurs", "typedoc", "destinataires"]

class PanDaFiReError(Exception):
    """Base de toutes les erreurs métier PanDaFiRe."""

class ValidationError(PanDaFiReError):
    """Données invalides fournies."""


class EntryExistsError(PanDaFiReError):
    """L'élément existe déjà."""
    def __init__(self, new_entry: str):
        self.username = new_entry # attribut accessible via e.username
        super().__init__(f"L'élément '{new_entry}' existe déjà.")


class JsonConfigNotFoundError(PanDaFiReError):
    """Fichier JSON de configuration introuvable."""
    def __init__(self, json_path: Path):
        self.json_path = json_path
        super().__init__(f"Fichier JSON de configuration introuvable : {json_path}")

class ProcessError(PanDaFiReError):
    """Erreur de traitement d'un PDF"""

class FileNotFoundError(ProcessError):
    pass

class FileAlreadyExistError(ProcessError):
    """La destination existe déjà, traitement annulé."""
    def __init__(self, destination: Path) -> None:
        self.destination = destination
        super().__init__(f"Fichier déjà existant : {destination.name}")

class Statut(Enum):
    RENOMME = "renommé"
    DEPLACE = "déplacé"
    DRY_RUN = "simulation"

# dataclass pour les paramètre de processor.py
@dataclass
class ProcessResult:
    source: Path
    statut : Statut
    destination: Path
    scores: dict = field(default_factory=dict) # pour le debug

# dataclass pour enrich.py et destinataire.py
@dataclass
class JsonNewEntryDraft():
    config_type: TypeDeConfig
    description: str # nom complet
    keywords: dict[str, int] # mot-clé + score d'importance
    json_path: Path
    category : str = ""
    keywords_ajustes: list[str] = field(default_factory=list) # pour éviter de réajouter les mêmes keywords
    overwrite : bool = False # pour forcer l'écrasement d'une entrée existante




