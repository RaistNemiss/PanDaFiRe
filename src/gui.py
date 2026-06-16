import customtkinter


# 1. Fenêtre principale
app = customtkinter.CTk()
app.title("PanDaFiRe 🐼🔥 by RaistNemiss")
app.geometry("400x150")
app.grid_columnconfigure(0, weight=1)
app.grid_columnconfigure(1, weight=1)





# 2. boutons

def select_file():
    chemin_fichier = customtkinter.filedialog.askopenfilename(title="Choisir un fichier PDF", filetypes=[("PDF", "*.pdf"), ("Tous", "*.*")])
    if chemin_fichier:
        print(chemin_fichier)

def select_folder():
    chemin_dossier = customtkinter.filedialog.askdirectory(title="Choisir un dossier")
    if chemin_dossier:
        print(chemin_dossier)

bouton_ficher = customtkinter.CTkButton(app, text="ouvrir un PDF", command=select_file)
bouton_ficher.grid(row= 0, column=0, padx=20, pady=20)

bouton_ficher = customtkinter.CTkButton(app, text="ouvrir un Dossier", command=select_folder)
bouton_ficher.grid(row= 0, column=1, padx=20, pady=20)

app.mainloop()