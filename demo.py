# demo_exceptions.py

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1) LES EXCEPTIONS PERSONNALISÉES (= des "types" de problèmes nommés)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ValidationError(Exception):
    """Données invalides fournies."""


class UserExistsError(Exception):
    """L'utilisateur existe déjà."""
    def __init__(self, username: str):
        self.username = username  # 📦 attribut accessible via e.username
        super().__init__(f"L'utilisateur '{username}' existe déjà.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2) LE SERVICE (pure logique métier, AUCUNE I/O — pas de print, pas d'input)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Faux "stockage" en mémoire
BASE_UTILISATEURS = {"alice", "bob"}


def ajouter_utilisateur(username: str, allow_overwrite: bool = False) -> str:
    """
    Tente d'ajouter un utilisateur.
    Lève ValidationError ou UserExistsError selon le problème.
    """
    # Validation
    if not username or not username.strip():
        raise ValidationError("Le nom d'utilisateur ne peut pas être vide.")
    if len(username) < 3:
        raise ValidationError("Le nom doit faire au moins 3 caractères.")

    # Doublon
    if username in BASE_UTILISATEURS and not allow_overwrite:
        raise UserExistsError(username)

    # Sauvegarde (ici on simule)
    BASE_UTILISATEURS.add(username)
    return username


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3) L'INTERFACE CLI (réagit aux exceptions à SA façon)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def cli_ajouter(username: str):
    print(f"\n🖥️  [CLI] Tentative d'ajout de : '{username}'")
    try:
        ajouter_utilisateur(username)
        print(f"✅ '{username}' ajouté !")
    except ValidationError as e:
        print(f"❌ Donnée invalide : {e}")
    except UserExistsError as e:
        # Simulation : on dit "oui, écrase"
        print(f"⚠️  {e}")
        reponse = "o"  # en vrai : input("Écraser ? (o/n) ")
        if reponse == "o":
            ajouter_utilisateur(e.username, allow_overwrite=True)
            print(f"♻️  '{e.username}' écrasé !")
        else:
            print("🚫 Annulé.")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4) UNE AUTRE INTERFACE (ex: API web) — réagit DIFFÉREMMENT aux mêmes erreurs
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def api_ajouter(username: str) -> dict:
    print(f"\n🌐 [API] POST /users  body={{'username': '{username}'}}")
    try:
        ajouter_utilisateur(username)
        return {"status": 201, "message": "created"}
    except ValidationError as e:
        return {"status": 400, "error": str(e)}
    except UserExistsError as e:
        return {"status": 409, "error": str(e), "username": e.username}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5) DÉMO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    # CLI
    cli_ajouter("charlie")   # ✅ ok
    cli_ajouter("")          # ❌ ValidationError
    cli_ajouter("al")        # ❌ ValidationError (trop court)
    cli_ajouter("alice")     # ⚠️  UserExistsError → écrase

    # API (même service, réactions différentes)
    print("\n" + "=" * 50)
    print(api_ajouter("david"))   # {"status": 201, ...}
    print(api_ajouter("xy"))      # {"status": 400, ...}
    print(api_ajouter("bob"))     # {"status": 409, ...}