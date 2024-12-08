import tkinter as tk
from tkinter import messagebox


class Lagersystem:
    def __init__(self):
        self.lagerbestand = {}
        self.automatenbestand = {}
        self.automat_befuellt = False

    def ware_hinzufuegen(self, barcode, name, menge):
        if barcode in self.lagerbestand:
            if self.lagerbestand[barcode]['name'] != name:
                messagebox.showerror(
                    "Fehler",
                    f"Der Barcode {barcode} ist bereits mit einem anderen Namen ({self.lagerbestand[barcode]['name']}) verknüpft!"
                )
                return
            self.lagerbestand[barcode]['menge'] += menge
        else:
            self.lagerbestand[barcode] = {'name': name, 'menge': menge}
        messagebox.showinfo("Erfolg", f"{menge} Einheiten von {name} hinzugefügt.")

    def automat_befuellen(self, barcode, menge):
        if barcode in self.lagerbestand and self.lagerbestand[barcode]['menge'] >= menge:
            if barcode in self.automatenbestand:
                self.automatenbestand[barcode]['menge'] += menge
            else:
                self.automatenbestand[barcode] = {'name': self.lagerbestand[barcode]['name'], 'menge': menge}
            self.lagerbestand[barcode]['menge'] -= menge
            self.automat_befuellt = True
            messagebox.showinfo("Erfolg", f"Automat mit {menge} Einheiten gefüllt.")
        else:
            self.automat_befuellt = False
            messagebox.showerror("Fehler", "Nicht genug Bestand oder falscher Barcode!")

    def ware_aus_automat_entnehmen(self, barcode, menge):
        if barcode in self.automatenbestand and self.automatenbestand[barcode]['menge'] >= menge:
            self.automatenbestand[barcode]['menge'] -= menge
            if self.automatenbestand[barcode]['menge'] == 0:
                del self.automatenbestand[barcode]
            return True
        return False


class GUI:
    def __init__(self, root, lagersystem):
        self.root = root
        self.lagersystem = lagersystem

        self.root.title("Lagersystem für Medikamente")
        self.root.geometry("800x600")

        self.build_gui()

    def build_gui(self):
        # Hauptfenster Layout
        frame_top = tk.Frame(self.root, pady=20)
        frame_top.pack()

        tk.Label(frame_top, text="Lagersystem für Medikamente", font=("Arial", 18)).pack()

        frame_middle = tk.Frame(self.root, pady=20)
        frame_middle.pack(fill=tk.BOTH, expand=True, padx=20)

        self.listbox = tk.Listbox(frame_middle, font=("Arial", 12), height=15)
        self.listbox.pack(fill=tk.BOTH, expand=True)

        frame_bottom = tk.Frame(self.root, pady=20)
        frame_bottom.pack()

        tk.Button(frame_bottom, text="Ware hinzufügen", font=("Arial", 12), command=self.ware_hinzufuegen_gui).pack(side=tk.LEFT, padx=10)
        tk.Button(frame_bottom, text="Automat befüllen", font=("Arial", 12), command=self.automat_befuellen_gui).pack(side=tk.LEFT, padx=10)
        tk.Button(frame_bottom, text="Automatenbestand anzeigen", font=("Arial", 12), command=self.automat_bestand_gui).pack(side=tk.LEFT, padx=10)
        tk.Button(frame_bottom, text="Aktualisieren", font=("Arial", 12), command=self.aktualisiere_liste).pack(side=tk.RIGHT, padx=10)

    def aktualisiere_liste(self):
        self.listbox.delete(0, tk.END)
        for barcode, info in self.lagersystem.lagerbestand.items():
            self.listbox.insert(tk.END, f"{info['name']} (Bestand: {info['menge']})")

    def ware_hinzufuegen_gui(self):
        def hinzufuegen(event=None):
            barcode = entry_barcode.get()
            name = entry_name.get()
            try:
                menge = int(entry_menge.get())
            except ValueError:
                messagebox.showerror("Fehler", "Bitte eine gültige Menge eingeben!")
                return
            self.lagersystem.ware_hinzufuegen(barcode, name, menge)
            self.aktualisiere_liste()
            fenster.destroy()

        fenster = tk.Toplevel()
        fenster.title("Ware hinzufügen")
        fenster.geometry("400x300")

        frame = tk.Frame(fenster, pady=10)
        frame.pack(fill=tk.BOTH)

        tk.Label(frame, text="Barcode:", font=("Arial", 12)).pack(anchor=tk.W, padx=20)
        entry_barcode = tk.Entry(frame, font=("Arial", 12))
        entry_barcode.pack(fill=tk.X, padx=20)

        tk.Label(frame, text="Name:", font=("Arial", 12)).pack(anchor=tk.W, padx=20, pady=(10, 0))
        entry_name = tk.Entry(frame, font=("Arial", 12))
        entry_name.pack(fill=tk.X, padx=20)

        tk.Label(frame, text="Menge:", font=("Arial", 12)).pack(anchor=tk.W, padx=20, pady=(10, 0))
        entry_menge = tk.Entry(frame, font=("Arial", 12))
        entry_menge.pack(fill=tk.X, padx=20)

        tk.Button(frame, text="Hinzufügen", font=("Arial", 12), command=hinzufuegen).pack(pady=20)

        fenster.bind("<Return>", hinzufuegen)

    def automat_befuellen_gui(self):
        def befuellen(event=None):
            barcode = entry_barcode.get()
            try:
                menge = int(entry_menge.get())
            except ValueError:
                messagebox.showerror("Fehler", "Bitte eine gültige Menge eingeben!")
                return
            self.lagersystem.automat_befuellen(barcode, menge)
            self.aktualisiere_liste()
            fenster.destroy()

        fenster = tk.Toplevel()
        fenster.title("Automat befüllen")
        fenster.geometry("400x300")

        frame = tk.Frame(fenster, pady=10)
        frame.pack(fill=tk.BOTH)

        tk.Label(frame, text="Barcode:", font=("Arial", 12)).pack(anchor=tk.W, padx=20)
        entry_barcode = tk.Entry(frame, font=("Arial", 12))
        entry_barcode.pack(fill=tk.X, padx=20)

        tk.Label(frame, text="Menge:", font=("Arial", 12)).pack(anchor=tk.W, padx=20, pady=(10, 0))
        entry_menge = tk.Entry(frame, font=("Arial", 12))
        entry_menge.pack(fill=tk.X, padx=20)

        tk.Button(frame, text="Befüllen", font=("Arial", 12), command=befuellen).pack(pady=20)

        fenster.bind("<Return>", befuellen)

    def automat_bestand_gui(self):
        def aktualisiere_automaten_liste():
            for widget in listbox_frame.winfo_children():
                widget.destroy()

            for barcode, info in self.lagersystem.automatenbestand.items():
                row = tk.Frame(listbox_frame)
                row.pack(fill=tk.X, pady=2)

                tk.Label(row, text=f"{info['name']} (Bestand: {info['menge']})", font=("Arial", 12)).pack(side=tk.LEFT)

                entry_menge = tk.Entry(row, font=("Arial", 12), width=5)
                entry_menge.pack(side=tk.RIGHT, padx=10)
                entry_menge.insert(0, "0")

                row.entry_menge = entry_menge
                row.barcode = barcode
                row.info = info

                listbox_frame.rows.append(row)

        def bestellung_aufgeben(event=None):
            gesamt_bestellung = []
            for row in listbox_frame.rows:
                try:
                    menge = int(row.entry_menge.get())
                    if menge > 0:
                        gesamt_bestellung.append((row.barcode, menge))
                except ValueError:
                    continue

            if not gesamt_bestellung:
                messagebox.showerror("Fehler", "Keine gültige Bestellung eingegeben!")
                return

            fehlgeschlagene_artikel = []
            for barcode, menge in gesamt_bestellung:
                if not self.lagersystem.ware_aus_automat_entnehmen(barcode, menge):
                    fehlgeschlagene_artikel.append(self.lagersystem.automatenbestand[barcode]['name'])

            if fehlgeschlagene_artikel:
                messagebox.showerror(
                    "Fehler",
                    f"Bestellung konnte für folgende Artikel nicht abgeschlossen werden:\n{', '.join(fehlgeschlagene_artikel)}"
                )
            else:
                messagebox.showinfo("Erfolg", "Die Bestellung wurde erfolgreich aufgegeben.")

            aktualisiere_automaten_liste()

        fenster = tk.Toplevel()
        fenster.title("Automatenbestand")
        fenster.geometry("600x400")

        frame_top = tk.Frame(fenster, pady=10)
        frame_top.pack(fill=tk.BOTH)

        tk.Label(frame_top, text="Automatenbestand", font=("Arial", 16)).pack()

        canvas = tk.Canvas(fenster)
        scrollbar = tk.Scrollbar(fenster, orient=tk.VERTICAL, command=canvas.yview)
        listbox_frame = tk.Frame(canvas)
        listbox_frame.rows = []

        listbox_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=listbox_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        frame_bottom = tk.Frame(fenster, pady=10)
        frame_bottom.pack()

        tk.Button(frame_bottom, text="Bestellung aufgeben", font=("Arial", 12), command=bestellung_aufgeben).pack(side=tk.LEFT, padx=10)
        tk.Button(frame_bottom, text="Aktualisieren", font=("Arial", 12), command=aktualisiere_automaten_liste).pack(side=tk.RIGHT, padx=10)

        fenster.bind("<Return>", bestellung_aufgeben)
        aktualisiere_automaten_liste()


# Initialisierung des Systems
if __name__ == "__main__":
    lagersystem = Lagersystem()
    root = tk.Tk()
    app = GUI(root, lagersystem)
    root.mainloop()
