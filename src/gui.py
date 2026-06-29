import customtkinter
from tkinter import messagebox
from pathlib import Path

from .processor import process_pdf
from .entry_service import (
    Statut,
    ProcessPdfResult,
    PanDaFiReError,
    ValidationError,
    EntryExistsError,
    TypeDeConfig,
    JsonNewEntryDraft,
)
from .config import prepare_nouvelle_entree
from .config_path import set_output_path, CONFIG_PATH
from .logger import log_run
from .utils import ajouter_nouvelle_entree_json


class DialogActions(customtkinter.CTkToplevel):
    """Boîte de dialogue pour les actions Enrich, Register, etc."""

    CHAMPS_PAR_TYPE = {
        "emetteurs": [
            ("nom_emetteur", "le nom de l'émetteur", True),
            ("email", "l'email", False),
            ("telephone", "le téléphone", False),
            ("site_web", "le site web", False),
            ("site_web_alt", "le site web alternatif", False),
            ("mots_cles", "des mots-clés supplémentaires", False),
        ],
        "destinataires": [
            ("prenom", "le prénom", True),
            ("nom", "le nom", True),
            ("email", "l'email", False),
            ("telephone", "le téléphone", False),
        ],
    }

    PATH_PAR_TYPE = {
        "emetteurs": Path(CONFIG_PATH / "emetteurs.json"),
        "destinataires": Path(CONFIG_PATH / "destinataire.json"),
    }

    def __init__(self, titre: str, type_de_config: TypeDeConfig):

        super().__init__()
        self.title(f"PanDaFiRe - {titre}")
        self.config_type: TypeDeConfig = type_de_config
        self.geometry("600x500")

        # ⚠️ garde la fenêtre AU-DESSUS de la principale
        self.transient()
        self.grab_set()  # bloque l'interaction avec la fenêtre principale

        label = customtkinter.CTkLabel(self, text=f"Configuration : {titre}")
        label.pack(padx=20, pady=(20, 10))

        noms_champs = self.CHAMPS_PAR_TYPE.get(self.config_type, [])
        # nom de champ par défaut si rien n'est entré
        if noms_champs is None:
            noms_champs = [("information", "une information", False)]

        self.champs = {}  # liste pour stocker les champs de saisie
        self._champs_obligatoires = [
            (cle, champ, obl) for cle, champ, obl in self.champs if obl
        ]  # crée la liste des champs obligatoires

        for cle, nom_champ, obligatoire in noms_champs:
            suffixe = " (obligatoire)" if obligatoire else ""
            champ = customtkinter.CTkEntry(
                self,
                placeholder_text=f"Entrer {nom_champ}{suffixe}...",
            )
            champ.pack(padx=20, pady=10, fill="x")
            self.champs[cle] = champ

            if obligatoire:
                champ.bind(
                    "<KeyRelease>", self._maj_etat_bouton
                )  # on surveille les frappes

        # démarre le bouton en état grisé s'il y a des champs obligatoires
        etat_bouton_initial = "disabled" if self._champs_obligatoires else "normal"
        self.bouton_valider = customtkinter.CTkButton(
            self, text="Valider", command=self._valider, state=etat_bouton_initial
        )
        self.bouton_valider.pack(padx=20, pady=20)

    def _maj_etat_bouton(self, *args):
        """vérife que tous les champs obligatoire soient remplis et change l'état du bouton valider en conséquence"""
        champs_obligatoires_tous_remplis = all(
            champ[cle].get().strip() for cle, champ, _ in self._champs_obligatoires
        )
        self.bouton_valider.configure(
            state="normal" if champs_obligatoires_tous_remplis else "disabled"
        )

    def _afficher_recap_confirmer(self, brouillon: JsonNewEntryDraft):
        """Construit un texte récapitulatif lisible pour la confirmation."""
        lignes = [
            f"Type : {brouillon.config_type}",
            f"Nom  : {brouillon.description}",
        ]
        if brouillon.keywords:
            lignes.append(f"Mots-clés : {brouillon.keywords}")
        lignes.append("\nConfirmer l'ajout ?")
        return "\n".join(lignes)

    def _valider(self):
        # 0. Récupérer les saisies (dict clé_métier → valeur)
        donnees = {cle: champ.get().strip() for cle, champ in self.champs.items()}

        # 👇 logique partagée (la fonction qu'on a extraite)
        nom_complet = construire_nom_complet(self.config_type, donnees)

        # 👇 json_path construit ICI, au bon moment 🎯
        json_path = self.PATH_PAR_TYPE[self.config_type]

        brouillon = JsonNewEntryDraft(
            config_type=self.config_type, 
            description=nom_complet, 
            keywords={}, 
            json_path=json_path,
        )

        # 1. Validation + vérification existence
        try:
            prepare_nouvelle_entree(brouillon)
        except ValidationError as e:
            messagebox.showerror("Erreur", str(e))
            return  # 👈 on reste dans le dialog
        except EntryExistsError as e:
            if not messagebox.askyesno("Doublon", f"{e}\nVoulez-vous l'écraser ?"):
                return
            brouillon.overwrite = True

        # 2. Saisie des mots-clés (à adapter en UI — voir note ci-dessous)
        # _ui_saisir_mots_cles(brouillon, ...)   🤔

        # 3. Récapitulatif + confirmation
        recap = self._afficher_recap_confirmer(brouillon)
        if not messagebox.askyesno("Confirmer", recap):
            return

        # 4. Ajout dans le JSON
        log(f"{brouillon.config_type},json a été mis à jour avec la nouvelle entrée {brouillon.description}") #DEBUG
        # try:
        #     ajouter_nouvelle_entree_json(brouillon)
        # except PanDaFiReError as e:
        #     messagebox.showerror("Échec", f"Échec de l'ajout : {e}")
        #     return
        # else:
        #     action = "mis à jour" if brouillon.overwrite else "ajouté"
        #     messagebox.showinfo("Succès", f"✅ '{nom_complet}' {action} !")
        #     self.destroy()  # 👈 ferme le dialog après succès 🎉


# logique à migrer ailleurs :
@log_run
def traiter_chemin_pdf(
    pdf_path: Path, dry_run: bool, recursive: bool, output: bool
) -> None:
    """Traite un fichier ou un dossier PDF en fonction des options fournies."""
    textbox.delete("1.0", "end")  # on vide la textbox avant chaque traitement

    if not pdf_path.exists():
        raise PanDaFiReError(f"⚠️ Le chemin n'existe pas : {pdf_path}")

    if pdf_path.is_file():
        _traiter_fichier(pdf_path, dry_run, debug=False, output=output)
    elif pdf_path.is_dir():
        _gui_traiter_dossier(pdf_path, dry_run, recursive, output)


def _gui_traiter_dossier(
    dossier: Path, dry_run: bool, recursive: bool, output: bool
) -> None:

    pdf_files = (
        list(dossier.rglob("*.pdf")) if recursive else list(dossier.glob("*.pdf"))
    )

    for pdf_file in pdf_files:
        try:
            _traiter_fichier(pdf_file, dry_run, debug=False, output=output)
        except PanDaFiReError as e:
            log(f"❌ Erreur sur {pdf_file.name} : {e}")


def _traiter_fichier(path: Path, dry_run: bool, debug: bool, output: bool) -> None:
    resultat = process_pdf(path, dry_run, debug, output)
    _gui_afficher_resultat(resultat)

def _gui_construire_recap():
    pass


def ouvrir_dialog(nom_action, type_de_config: TypeDeConfig) -> None:
    """Ouvre une boîte de dialogue pour l'action spécifiée."""
    DialogActions(nom_action, type_de_config)

# fonction partagée CLI + UI
def construire_nom_complet(type_de_config : TypeDeConfig, donnees: dict) -> str:
    if type_de_config == "destinataires":
        return f"{donnees['prenom']} {donnees['nom']}".strip()
    if type_de_config == "emetteurs":
        return donnees["nom_emetteur"]
    raise ValidationError(f"Type non géré : {type_de_config}")


def selection_fichier() -> None:
    chemin = customtkinter.filedialog.askopenfilename(
        title="Choisir un fichier PDF", filetypes=[("PDF", "*.pdf"), ("Tous", "*.*")]
    )
    if chemin:  # ⚠️ l'utilisateur peut annuler !
        chemin_entry.delete(0, "end")  # on vide d'abord
        chemin_entry.insert(0, chemin)  # puis on écrit


def selection_dossier() -> None:
    chemin = customtkinter.filedialog.askdirectory(title="Choisir un dossier")
    if chemin:
        chemin_entry.delete(0, "end")
        chemin_entry.insert(0, chemin)


def set_output() -> None:
    chemin = customtkinter.filedialog.askdirectory(title="Choisir le dossier de sortie")
    if not chemin:  # ⚠️ l'utilisateur a annulé
        return

    nouveau_path = Path(chemin)
    set_output_path(nouveau_path)  # 💾 ta fonction qui sauvegarde dans settings.json
    log(f"📁 Dossier de sortie défini : {nouveau_path.resolve()}")


def _gui_afficher_resultat(resultat: ProcessPdfResult) -> None:
    """Affiche le résultat du traitement dans la zone de texte."""
    message = {
        Statut.RENOMME: f"✅ {resultat.source.name} → {resultat.destination.name}",
        Statut.DEPLACE: f"✅ {resultat.source.name} déplacé vers",
        Statut.DRY_RUN: f"[Dry-Run] {resultat.source.name} → {resultat.destination.name}",
    }
    log(message[resultat.statut])


def log(message: str) -> None:
    """Affiche un message dans la zone de texte."""
    textbox.insert("end", message + "\n")
    textbox.see("end")  # scroll automatique vers le bas
    textbox.update_idletasks()  # 🔄 force le rafraîchissement immédiat


app = customtkinter.CTk()
app.title("PanDaFiRe 🐼🔥 by RaistNemiss")
app.geometry("900x500")
app.minsize(650, 350)

app.grid_columnconfigure(0, weight=0)  # frame gauche (contrôles)
app.grid_columnconfigure(1, weight=2)  # textbox (le gros morceau)
app.grid_columnconfigure(2, weight=0)  # frame actions (largeur fixe)
app.grid_rowconfigure(0, weight=1)  # une seule ligne dans app maintenant !

# ─── FRAME GAUCHE : conteneur des contrôles ───
frame_gauche = customtkinter.CTkFrame(app)
frame_gauche.grid(row=0, column=0, padx=20, pady=20, sticky="ns")

# Les widgets sont placés DANS frame_gauche (pas dans app !)
bouton_fichier = customtkinter.CTkButton(
    frame_gauche, text="ouvrir fichier...", command=selection_fichier
)
bouton_fichier.grid(row=0, column=0, padx=15, pady=(15, 5), sticky="ew")

bouton_dossier = customtkinter.CTkButton(
    frame_gauche, text="ouvrir dossier...", command=selection_dossier
)
bouton_dossier.grid(row=1, column=0, padx=15, pady=5, sticky="ew")

var_dryrun = customtkinter.BooleanVar(value=False)
check_dryrun = customtkinter.CTkCheckBox(
    frame_gauche, text="Dry-run", onvalue=True, offvalue=False, variable=var_dryrun
)
check_dryrun.grid(row=2, column=0, padx=15, pady=5, sticky="w")

var_recursive = customtkinter.BooleanVar(value=False)
check_recursive = customtkinter.CTkCheckBox(
    frame_gauche, text="Recursive", onvalue=True, offvalue=False, variable=var_recursive
)
check_recursive.grid(row=3, column=0, padx=15, pady=5, sticky="w")

var_output = customtkinter.BooleanVar(value=False)
check_output = customtkinter.CTkCheckBox(
    frame_gauche, text="output", onvalue=True, offvalue=False, variable=var_output
)
check_output.grid(row=4, column=0, padx=15, pady=5, sticky="w")

bouton_process = customtkinter.CTkButton(
    frame_gauche,
    text="🚀 PROCESS",
    command=lambda: traiter_chemin_pdf(
        Path(chemin_entry.get()),
        var_dryrun.get(),
        var_recursive.get(),
        var_output.get(),
    ),
)
bouton_process.grid(row=5, column=0, padx=15, pady=(15, 15), sticky="ew")

# ─── COLONNE DROITE : chemin + résultat (toujours dans app) ───
chemin_entry = customtkinter.CTkEntry(
    app, placeholder_text="chemin du fichier ou du dossier"
)
chemin_entry.grid(row=0, column=1, padx=0, pady=(20, 5), sticky="new")

textbox = customtkinter.CTkTextbox(app)
textbox.grid(row=0, column=1, padx=0, pady=(60, 20), sticky="nsew")

# ─── FRAME DROITE : actions ───
frame_actions = customtkinter.CTkFrame(app)
frame_actions.grid(row=0, column=2, padx=20, pady=20, sticky="ns")

btn_enrich = customtkinter.CTkButton(
    frame_actions, text="Enrich", command=lambda: ouvrir_dialog("Enrich","emetteurs")
)
btn_enrich.grid(row=0, column=0, padx=15, pady=(15, 5))

btn_register = customtkinter.CTkButton(
    frame_actions,
    text="Register",
    command=lambda: ouvrir_dialog("Register", "destinataires"),
)
btn_register.grid(row=1, column=0, padx=15, pady=5)

btn_manual_enrich = customtkinter.CTkButton(
    frame_actions,
    text="Manual Enrich",
    command=lambda: ouvrir_dialog("Manual Enrich", "emetteurs"),
)
btn_manual_enrich.grid(row=2, column=0, padx=15, pady=5)

btn_output = customtkinter.CTkButton(
    frame_actions, text="Set Output", command=set_output
)
btn_output.grid(row=3, column=0, padx=15, pady=5)


app.mainloop()
