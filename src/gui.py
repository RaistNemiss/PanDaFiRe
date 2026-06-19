import customtkinter
from pathlib import Path

from .processor import process_pdf
from .entry_service import Statut, ProcessPdfResult


class DialogActions(customtkinter.CTkToplevel):
    """Boîte de dialogue pour les actions Enrich, Register, Set Output, etc."""

    def __init__(self, titre):
        super().__init__()
        self.title(f"PanDaFiRe - {titre}")
        self.geometry("600x250")

        # ⚠️ garde la fenêtre AU-DESSUS de la principale
        self.transient()
        self.grab_set()  # bloque l'interaction avec la fenêtre principale

        label = customtkinter.CTkLabel(self, text=f"Configuration : {titre}")
        label.pack(padx=20, pady=(20, 10))

        self.champ = customtkinter.CTkEntry(self, placeholder_text="entrez une info...")
        self.champ.pack(padx=20, pady=10, fill="x")

        btn_valider = customtkinter.CTkButton(
            self, text="Valider", command=self.valider
        )
        btn_valider.pack(padx=20, pady=20)

    def valider(self):
        valeur = self.champ.get()
        print(f"Saisi : {valeur}")  # plus tard → appel de ton métier
        self.destroy()  # ferme la boîte


def ouvrir_dialog(nom_action):
    DialogActions(nom_action)


def selection_fichier():
    chemin = customtkinter.filedialog.askopenfilename(
        title="Choisir un fichier PDF", filetypes=[("PDF", "*.pdf"), ("Tous", "*.*")]
    )
    if chemin:  # ⚠️ l'utilisateur peut annuler !
        chemin_entry.delete(0, "end")  # on vide d'abord
        chemin_entry.insert(0, chemin)  # puis on écrit


def selection_dossier():
    chemin = customtkinter.filedialog.askdirectory(title="Choisir un dossier")
    if chemin:
        chemin_entry.delete(0, "end")
        chemin_entry.insert(0, chemin)


def _traiter_fichier(path: Path, dry_run: bool, debug: bool, output: bool) -> None:
    resultat = process_pdf(path, dry_run, debug, output)
    _gui_afficher_resultat(resultat)


def _gui_afficher_resultat(resultat: ProcessPdfResult):

    message = {
        Statut.RENOMME: f"✅ {resultat.source.name} → {resultat.destination.name}",
        Statut.DEPLACE: f"✅ {resultat.source.name} déplacé vers",
        Statut.DRY_RUN: f"[Dry-Run] {resultat.source.name} → {resultat.destination.name}",
    }
    log(message[resultat.statut])


def log(message: str):
    textbox.insert("end", message + "\n")
    textbox.see("end")  # scroll automatique vers le bas


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

check_dryrun = customtkinter.CTkCheckBox(frame_gauche, text="Dry-run")
check_dryrun.grid(row=2, column=0, padx=15, pady=5, sticky="w")

check_recursive = customtkinter.CTkCheckBox(frame_gauche, text="Recursive")
check_recursive.grid(row=3, column=0, padx=15, pady=5, sticky="w")

check_output = customtkinter.CTkCheckBox(frame_gauche, text="output")
check_output.grid(row=4, column=0, padx=15, pady=5, sticky="w")

bouton_process = customtkinter.CTkButton(frame_gauche, text="PROCESS")
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
    frame_actions, text="Enrich", command=lambda: ouvrir_dialog("Enrich")
)
btn_enrich.grid(row=0, column=0, padx=15, pady=(15, 5))

btn_register = customtkinter.CTkButton(
    frame_actions, text="Manual Enrich", command=lambda: ouvrir_dialog("Manual Enrich")
)
btn_register.grid(row=1, column=0, padx=15, pady=5)

btn_output = customtkinter.CTkButton(
    frame_actions, text="Register", command=lambda: ouvrir_dialog("Register")
)
btn_output.grid(row=2, column=0, padx=15, pady=5)

btn_autre = customtkinter.CTkButton(
    frame_actions, text="Set Output", command=lambda: ouvrir_dialog("Set Output")
)
btn_autre.grid(row=3, column=0, padx=15, pady=5)


app.mainloop()


# # 5. Bouton Process
# def process():
#     chemin = chemin_var.get()
#     if not chemin:
#         print("⚠️ Aucun chemin sélectionné")
#         return
#     traiter_chemin_pdf(Path(chemin), dry_run_var.get(), recursive_var.get())

# bouton_process = customtkinter.CTkButton(app, text="Process 🚀", command=process)
# bouton_process.grid(row=3, column=1, padx=20, pady=20)


# logique à migrer ailleurs :
def traiter_chemin_pdf(pdf_path: Path, dry_run: bool, recursive: bool):
    if pdf_path.is_file():
        print(f"Traitement du fichier : {pdf_path} (dry_run={dry_run})")
    elif pdf_path.is_dir():
        pattern = "**/*.pdf" if recursive else "*.pdf"
        liste = list(pdf_path.glob(pattern))
        print(
            f"Dossier avec {len(liste)} PDF (dry_run={dry_run}, recursive={recursive})"
        )
