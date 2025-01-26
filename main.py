import streamlit as st
import pandas as pd
import sqlite3

class Lagersystem:
    def __init__(self):
        self.db_conn = sqlite3.connect('lagerbestand.db')
        self.cursor = self.db_conn.cursor()
        self._initialize_database()

    def _initialize_database(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS lagerbestand (
                barcode TEXT PRIMARY KEY,
                name TEXT,
                menge INTEGER
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS automatenbestand (
                barcode TEXT PRIMARY KEY,
                name TEXT,
                menge INTEGER,
                FOREIGN KEY (barcode) REFERENCES lagerbestand(barcode)
            )
        ''')
        self.db_conn.commit()

    def ware_hinzufuegen(self, barcode, name):
        self.cursor.execute("SELECT * FROM lagerbestand WHERE barcode = ?", (barcode,))
        row = self.cursor.fetchone()
        if row:
            return f"Fehler: Der Barcode {barcode} existiert bereits im Lagerbestand und ist mit dem Namen {row[1]} verknüpft!"
        else:
            self.cursor.execute("INSERT INTO lagerbestand (barcode, name, menge) VALUES (?, ?, 1)", (barcode, name))
            self.db_conn.commit()
            return f"Erfolg: 1 Einheit von {name} hinzugefügt."

    def automat_befuellen(self, barcode):
        menge = 1  # Menge ist fest auf 1 gesetzt
        self.cursor.execute("SELECT * FROM lagerbestand WHERE barcode = ?", (barcode,))
        row = self.cursor.fetchone()
        if row and row[2] >= menge:
            self.cursor.execute("SELECT * FROM automatenbestand WHERE barcode = ?", (barcode,))
            automat_row = self.cursor.fetchone()
            if automat_row:
                neue_menge = automat_row[2] + menge
                self.cursor.execute("UPDATE automatenbestand SET menge = ? WHERE barcode = ?", (neue_menge, barcode))
            else:
                self.cursor.execute("INSERT INTO automatenbestand (barcode, name, menge) VALUES (?, ?, ?)", (barcode, row[1], menge))
            neue_lager_menge = row[2] - menge
            if neue_lager_menge == 0:
                self.cursor.execute("DELETE FROM lagerbestand WHERE barcode = ?", (barcode,))
            else:
                self.cursor.execute("UPDATE lagerbestand SET menge = ? WHERE barcode = ?", (neue_lager_menge, barcode))
            self.db_conn.commit()
            return f"Erfolg: Automat mit {menge} Einheiten gefüllt."
        return "Fehler: Nicht genug Bestand oder falscher Barcode!"

    def ware_aus_automat_entnehmen(self, barcode, menge):
        self.cursor.execute("SELECT * FROM automatenbestand WHERE barcode = ?", (barcode,))
        row = self.cursor.fetchone()
        if row and row[2] >= menge:
            neue_menge = row[2] - menge
            if neue_menge == 0:
                self.cursor.execute("DELETE FROM automatenbestand WHERE barcode = ?", (barcode,))
            else:
                self.cursor.execute("UPDATE automatenbestand SET menge = ? WHERE barcode = ?", (neue_menge, barcode))
            self.db_conn.commit()
            return "Erfolg: Ware entnommen."
        return "Fehler: Nicht genug Ware im Automaten."

    def loesche_ware(self, barcode):
        self.cursor.execute("DELETE FROM lagerbestand WHERE barcode = ?", (barcode,))
        self.cursor.execute("DELETE FROM automatenbestand WHERE barcode = ?", (barcode,))
        self.db_conn.commit()
        return f"Erfolg: Ware mit Barcode {barcode} wurde gelöscht."

    def aktualisiere_menge(self, barcode, neue_menge):
        self.cursor.execute("UPDATE lagerbestand SET menge = ? WHERE barcode = ?", (neue_menge, barcode))
        self.db_conn.commit()
        return f"Erfolg: Menge für Barcode {barcode} wurde auf {neue_menge} aktualisiert."

    def get_lagerbestand(self, filter_ort=None):
        lager_query = "SELECT barcode, name, menge, 'Lager' as ort FROM lagerbestand"
        automat_query = "SELECT barcode, name, menge, 'Automat' as ort FROM automatenbestand"

        if filter_ort == "Lager":
            self.cursor.execute(lager_query)
            data = self.cursor.fetchall()
        elif filter_ort == "Automat":
            self.cursor.execute(automat_query)
            data = self.cursor.fetchall()
        else:
            self.cursor.execute(f"{lager_query} UNION {automat_query} ORDER BY ort")
            data = self.cursor.fetchall()

        unique_data = {}
        for entry in data:
            if entry[0] not in unique_data:
                unique_data[entry[0]] = entry

        return pd.DataFrame(unique_data.values(), columns=["Barcode", "Name", "Menge", "Ort"])

# Initialisierung
lagersystem = Lagersystem()

# Streamlit GUI
st.set_page_config(page_title="Lagersystem für Medikamente", layout="wide")
st.title("Lagersystem für Medikamente")

# Auswahl des Tabs
menu = ["Lagerbestand anzeigen", "Ware hinzufügen", "Automat befüllen", "Bestellung aufgeben", "Ware löschen", "Menge aktualisieren"]
choice = st.sidebar.selectbox("Navigation", menu)

if choice == "Lagerbestand anzeigen":
    st.header("Lagerbestand")
    filter_option = st.selectbox("Ort filtern", ["Alle", "Lager", "Automat"], index=0)
    filter_ort = None if filter_option == "Alle" else filter_option
    lager_data = lagersystem.get_lagerbestand(filter_ort=filter_ort)

    if not lager_data.empty:
        st.table(lager_data)
    else:
        st.info("Der Lagerbestand ist leer.")

elif choice == "Ware hinzufügen":
    st.header("Ware hinzufügen")
    barcode = st.text_input("Barcode", key="barcode_hinzufuegen")
    name = st.text_input("Name", key="name_hinzufuegen")

    if st.button("Hinzufügen"):
        if barcode and name:
            message = lagersystem.ware_hinzufuegen(barcode, name)
            if "Erfolg" in message:
                st.success(message)
            else:
                st.error(message)

elif choice == "Automat befüllen":
    st.header("Automat befüllen")
    barcode = st.text_input("Barcode", key="barcode_befuell")
    if st.button("Befüllen"):
        if barcode:
            message = lagersystem.automat_befuellen(barcode)
            if "Erfolg" in message:
                st.success(message)
            else:
                st.error(message)

elif choice == "Bestellung aufgeben":
    st.header("Bestellung aufgeben")
    barcode = st.text_input("Barcode", key="barcode_bestellung")
    menge = st.number_input("Menge", min_value=1, step=1, key="menge_bestellung")
    if st.button("Bestellung aufgeben"):
        if barcode:
            message = lagersystem.ware_aus_automat_entnehmen(barcode, int(menge))
            if "Erfolg" in message:
                st.success(message)
            else:
                st.error(message)

elif choice == "Ware löschen":
    st.header("Ware löschen")
    barcode = st.text_input("Barcode", key="barcode_loeschen")
    if st.button("Löschen"):
        if barcode:
            message = lagersystem.loesche_ware(barcode)
            if "Erfolg" in message:
                st.success(message)
            else:
                st.error(message)

elif choice == "Menge aktualisieren":
    st.header("Menge aktualisieren")
    barcode = st.text_input("Barcode", key="barcode_aktualisieren")
    neue_menge = st.number_input("Neue Menge", min_value=0, step=1, key="menge_aktualisieren")
    if st.button("Aktualisieren"):
        if barcode:
            message = lagersystem.aktualisiere_menge(barcode, int(neue_menge))
            if "Erfolg" in message:
                st.success(message)
            else:
                st.error(message)
