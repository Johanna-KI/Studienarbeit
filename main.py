import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

class Lagersystem:
    def __init__(self):
        self.lagerbestand = {}
        self.automatenbestand = {}
        self.automat_befuellt = False

    def ware_hinzufuegen(self, barcode, name):
        if barcode in self.lagerbestand:
            if self.lagerbestand[barcode]['name'] != name:
                messagebox.showerror(
                    "Fehler",
                    f"Der Barcode {barcode} ist bereits mit einem anderen Namen ({self.lagerbestand[barcode]['name']}) verknüpft!"
                )
                return
            self.lagerbestand[barcode]['menge'] += 1
        else:
            self.lagerbestand[barcode] = {'name': name, 'menge': 1}
        messagebox.showinfo("Erfolg", f"1 Einheit von {name} hinzugefügt.")

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

    def berechne_gesamtmenge(self, name):
        gesamtmenge = sum(info['menge'] for info in self.lagerbestand.values() if info['name'] == name)
        return gesamtmenge

class GUI:
    def __init__(self, root, lagersystem):
        self.root = root
        self.lagersystem = lagersystem

        self.root.title("Lagersystem für Medikamente")
        self.root.geometry("800x600")

        self.build_gui()

    def build_gui(self):
        frame_top = tk.Frame(self.root, pady=20)
        frame_top.pack()

        tk.Label(frame_top, text="Lagersystem für Medikamente", font=("Arial", 18)).pack()

        frame_middle = tk.Frame(self.root, pady=20)
        frame_middle.pack(fill=tk.BOTH, expand=True, padx=20)

        self.tree = ttk.Treeview(frame_middle, columns=("Barcode", "Name", "Menge"), show="headings", height=15)
        self.tree.heading("Barcode", text="Barcode")
        self.tree.heading("Name", text="Name")
        self.tree.heading("Menge", text="Menge")

        self.tree.column("Barcode", width=150, anchor="center")
        self.tree.column("Name", width=300, anchor="w")
        self.tree.column("Menge", width=100, anchor="center")

        self.tree.pack(fill=tk.BOTH, expand=True)

        frame_bottom = tk.Frame(self.root, pady=20)
        frame_bottom.pack()

        tk.Button(frame_bottom, text="Ware hinzufügen", font=("Arial", 12), command=self.ware_hinzufuegen_gui).pack(side=tk.LEFT, padx=10)
        tk.Button(frame_bottom, text="Automat befüllen", font=("Arial", 12), command=self.automat_befuellen_gui).pack(side=tk.LEFT, padx=10)
        tk.Button(frame_bottom, text="Lagerbestand anzeigen", font=("Arial", 12), command=self.lagerbestand_anzeigen_gui).pack(side=tk.LEFT, padx=10)
        tk.Button(frame_bottom, text="Bestellung aufgeben", font=("Arial", 12), command=self.bestellung_aufgeben_gui).pack(side=tk.RIGHT, padx=10)

    def aktualisiere_tabelle(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        for barcode, info in self.lagersystem.lagerbestand.items():
            self.tree.insert("", tk.END, values=(barcode, info['name'], info['menge']))

    def lagerbestand_anzeigen_gui(self):
        fenster = tk.Toplevel()
        fenster.title("Lagerbestand")
        fenster.geometry("400x300")

        frame = tk.Frame(fenster, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)

        tree = ttk.Treeview(frame, columns=("Name", "Gesamtmenge"), show="headings", height=15)
        tree.heading("Name", text="Name")
        tree.heading("Gesamtmenge", text="Gesamtmenge")

        tree.column("Name", width=200, anchor="w")
        tree.column("Gesamtmenge", width=100, anchor="center")

        tree.pack(fill=tk.BOTH, expand=True)

        gesamtmengen = {}
        for info in self.lagersystem.lagerbestand.values():
            name = info['name']
            if name not in gesamtmengen:
                gesamtmengen[name] = self.lagersystem.berechne_gesamtmenge(name)

        for name, menge in gesamtmengen.items():
            tree.insert("", tk.END, values=(name, menge))

    def bestellung_aufgeben_gui(self):
        def aufgeben(event=None):
            barcode = entry_barcode.get()
            try:
                menge = int(entry_menge.get())
            except ValueError:
                messagebox.showerror("Fehler", "Bitte eine gültige Menge eingeben!")
                return

            if self.lagersystem.ware_aus_automat_entnehmen(barcode, menge):
                messagebox.showinfo("Erfolg", "Die Bestellung wurde erfolgreich aufgegeben.")
            else:
                messagebox.showerror("Fehler", "Die Bestellung konnte nicht ausgeführt werden.")

            fenster.destroy()

        fenster = tk.Toplevel()
        fenster.title("Bestellung aufgeben")
        fenster.geometry("400x300")

        frame = tk.Frame(fenster, pady=10)
        frame.pack(fill=tk.BOTH)

        tk.Label(frame, text="Barcode:", font=("Arial", 12)).pack(anchor=tk.W, padx=20)
        entry_barcode = tk.Entry(frame, font=("Arial", 12))
        entry_barcode.pack(fill=tk.X, padx=20)

        tk.Label(frame, text="Menge:", font=("Arial", 12)).pack(anchor=tk.W, padx=20, pady=(10, 0))
        entry_menge = tk.Entry(frame, font=("Arial", 12))
        entry_menge.pack(fill=tk.X, padx=20)

        tk.Button(frame, text="Aufgeben", font=("Arial", 12), command=aufgeben).pack(pady=20)

        fenster.bind("<Return>", aufgeben)

    def ware_hinzufuegen_gui(self):
        def hinzufuegen(event=None):
            barcode = entry_barcode.get()
            name = entry_name.get()
            self.lagersystem.ware_hinzufuegen(barcode, name)
            self.aktualisiere_tabelle()
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
            self.aktualisiere_tabelle()
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

# Initialisierung des Systems
if __name__ == "__main__":
    lagersystem = Lagersystem()
    root = tk.Tk()
    app = GUI(root, lagersystem)
    root.mainloop()
