from pathlib import Path
from collections import Counter


def candidats_fréquents(logs: list[dict]) -> list[tuple[str, int]]:

    emetteurs = []
    seuil_occurrence = 5  # seuil de fréquence pour considérer un candidat comme pertinent

    for log in logs:
            emetteurs.extend(log.get("emetteur_candidats", []))

    counter = Counter(emetteurs)
    
    return [
        (emetteur, occurrence) 
        for emetteur, occurrence in counter.most_common() 
        if occurrence >= seuil_occurrence]