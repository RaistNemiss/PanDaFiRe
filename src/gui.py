import customtkinter
from pathlib import Path

# 1. Fenêtre principale
app = customtkinter.CTk()
app.title("PanDaFiRe 🐼🔥 by RaistNemiss")
app.geometry("500x350")
app.grid_columnconfigure(0, weight=1)

# --- Variables liées ---
chemin_var = customtkinter.StringVar(value="")
dry_run_var = customtkinter.BooleanVar(value=False)
recursive_var = customtkinter.BooleanVar(value=False)

# 2. Sélection de chemin
def select_file():
    chemin = customtkinter.filedialog.askopenfilename(
        title="Choisir un fichier PDF", filetypes=[("PDF", "*.pdf"), ("Tous", "*.*")]
    )
    if chemin:
        chemin_var.set(chemin)        # ← met à jour l'entry automatiquement

def select_folder():
    chemin = customtkinter.filedialog.askdirectory(title="Choisir un dossier")
    if chemin:
        chemin_var.set(chemin)

# --- Frame boutons d'ouverture ---
frame_bouton = customtkinter.CTkFrame(app)
frame_bouton.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
frame_bouton.grid_columnconfigure((0, 1), weight=1)

bouton_fichier = customtkinter.CTkButton(frame_bouton, text="ouvrir un PDF", command=select_file)
bouton_fichier.grid(row=0, column=0, padx=10, pady=10)
bouton_dossier = customtkinter.CTkButton(frame_bouton, text="ouvrir un Dossier", command=select_folder)
bouton_dossier.grid(row=0, column=1, padx=10, pady=10)

# 3. Entry qui affiche le chemin
entry_chemin = customtkinter.CTkEntry(
    app, textvariable=chemin_var, placeholder_text="Aucun chemin sélectionné..."
)
entry_chemin.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

# 4. Checkboxes
frame_options = customtkinter.CTkFrame(app)
frame_options.grid(row=2, column=0, padx=20, pady=10, sticky="ew")

check_dry_run = customtkinter.CTkCheckBox(frame_options, text="Dry-run", variable=dry_run_var)
check_dry_run.grid(row=0, column=0, padx=20, pady=10)
check_recursive = customtkinter.CTkCheckBox(frame_options, text="Récursif", variable=recursive_var)
check_recursive.grid(row=0, column=1, padx=20, pady=10)

# 5. Bouton Process
def process():
    chemin = chemin_var.get()
    if not chemin:
        print("⚠️ Aucun chemin sélectionné")
        return
    traiter_chemin_pdf(Path(chemin), dry_run_var.get(), recursive_var.get())

bouton_process = customtkinter.CTkButton(app, text="Process 🚀", command=process)
bouton_process.grid(row=3, column=0, padx=20, pady=20)

# logique à migrer ailleurs :
def traiter_chemin_pdf(pdf_path: Path, dry_run: bool, recursive: bool):
    if pdf_path.is_file():
        print(f"Traitement du fichier : {pdf_path} (dry_run={dry_run})")
    elif pdf_path.is_dir():
        pattern = "**/*.pdf" if recursive else "*.pdf"
        liste = list(pdf_path.glob(pattern))
        print(f"Dossier avec {len(liste)} PDF (dry_run={dry_run}, recursive={recursive})")

app.mainloop()