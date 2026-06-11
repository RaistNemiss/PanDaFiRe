from pathlib import Path
from dataclasses import dataclass, field
from typing import Literal


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
        
@dataclass
class JsonNewEntryDraft():
    config_type: TypeDeConfig
    description: str # nom complet
    keywords: dict[str, int] # mot-clé + score d'importance
    json_path: Path
    category : str = ""
    keywords_ajustes: list[str] = field(default_factory=list) # pour éviter de réajouter les mêmes keywords
    overwrite : bool = False # pour forcer l'écrasement d'une entrée existante




