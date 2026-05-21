import json
from pathlib import Path


def chargement_destinataires(path: Path, debug: bool = False) -> dict:
    
    # Initialisation de la configuration des destinataires (création du fichier destinataire.json s'il n'existe pas déjà)
    init_destinataire_config(path, debug=debug)

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def init_destinataire_config(path: Path, debug: bool = False) -> None:
    
    # créer le dossier si nécessaire
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        return

    if debug:
        print("⚠️ destinataire.json introuvable → création du fichier")

    data = {
        "homer_simpson": {
            "description": "Homer Simpson",
            "keywords": {
                "homer simpson": 5,
                "simpson": 4,
                "homer": 3,
                "homer.simpson@email.com": 6,
                "+41 77 777 77 77": 6                
            }
        }
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    if debug:
        print("✅ destinataire.json créé avec un utilisateur exemple")

def determiner_initiales_destinataire(nom: str) -> str:
    
    if nom == "inconnu" or nom == "":
        return ""
    
    # extraire les initiales du nom du destinataire (ex: "Homer Simpson" → "HS") pour maximiser les chances de correspondance même si le nom complet n'est pas mentionné dans le document
    mots = nom.split()
    
    if len(mots) == 2:
        return (mots[0][:1] + mots[1][:2]).upper()  # Prend la première lettre du premier mot et les deux premières lettres du second mot (ex: Homer Simpson → HSI)
    if len(mots) == 1:
        return nom[:2].upper()  # si le nom ne comporte qu'un mot, prendre les 2 premières lettres comme initiales
    else:
        return "".join(mot[0] for mot in mots).upper()  # sinon, prendre la première lettre de chaque mot (ex: Jean Claude Van Damme → JCVD)