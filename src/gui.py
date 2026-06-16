import customtkinter


# 1. Fenêtre principale
app = customtkinter.CTk()
app.title("PanDaFire 🐼🔥 by RaistNemiss")
app.geometry("400x150")



# 2. bouton

def action_bouton():
    print("bouton pressé")
bouton = customtkinter.CTkButton(app, text="ouvrir...", command=action_bouton)

bouton.grid(row= 0, column=0, padx=20, pady=20)

app.mainloop()