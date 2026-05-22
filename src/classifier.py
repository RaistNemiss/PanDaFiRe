import re
from typing import overload, Literal

from .utils import normaliser_text

@overload
def identifier_par_score(
    texte: str, config: dict, seuil: int = 4, 
    retour_score: Literal[False] = False, seuil_confiance: int = 3
    ) -> str: ...

@overload
def identifier_par_score(
    texte: str, config: dict, seuil: int = 4, 
    retour_score: Literal[True] = ..., seuil_confiance: int = 3
    ) -> tuple[str, dict[str, int]]: ...

def identifier_par_score(
        texte: str, 
        config: dict, 
        seuil: int = 4, 
        retour_score: bool = False, 
        seuil_confiance: int = 3
        ) -> str | tuple[str, dict[str, int]] :
    
    # vérification de la présence de la configuration pour éviter les erreurs d'exécution si elle est absente ou mal formée
    if not config:
        return ("inconnu", {}) if retour_score else "inconnu"

    
    # création d'une compréhension de dictionnaire pour compter les occurrences de mots-clés pour chaque type de document
    scores = {cle: 0 for cle in config}
    

    for cle, data in config.items():
        mots_cle = data["keywords"]
        for mot, valeur_mot in mots_cle.items():
            mot_normalise = normaliser_text(mot, stopwords=False)
            if len(mot_normalise) < 3:  # éviter que les mots trop court génère des faux positifs (ex: UBS dans sUBScription)
                nombre_occurrences = len(re.findall(rf"(?<!\w){re.escape(mot_normalise)}(?!\w)", texte))
            else:
                nombre_occurrences = len(re.findall(rf"\b{re.escape(mot_normalise)}\b", texte))

            scores[cle] += nombre_occurrences * int(valeur_mot)
   
    # Vérifier l'écart avec le 2ème meilleur score
    scores_tries = sorted(scores.items(), key=lambda x:x[1], reverse=True) # transforme le dictionnaire en liste trié selon le nombre d'occurrence.
    gagnant, meilleur_score = scores_tries[0]
    deuxieme_score = scores_tries[1][1] if len(scores_tries) > 1 else 0

    #calcul de l'écart significatif entre les scores
    ecart = meilleur_score - deuxieme_score
    resultat = gagnant if meilleur_score >= seuil and ecart >= seuil_confiance else  "inconnu"
    
    if retour_score:
        return (resultat, scores)
    
    return resultat