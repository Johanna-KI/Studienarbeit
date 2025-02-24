import streamlit as st
import pandas as pd
import sqlite3
import bcrypt
import time
import csv
import random
from datetime import datetime
from warnung import Warnung  # Ensure you import the Warnung class
from datenbank import Datenbank

class Lager:
    def __init__(self):
        self.db_conn = sqlite3.connect('lagerbestand.db', check_same_thread=False)
        self.cursor = self.db_conn.cursor()
        self.warnung = Warnung()  # Instantiate Warnung to access its methods
        self.datenbank = Datenbank()

    def ware_hinzufuegen(self, barcode, name, verfallsdatum, ort='Lager'):
        """Fügt eine Ware zum Lagerbestand hinzu, aber blockiert doppelte Barcodes in offenen Bestellungen."""
        try:
            if not barcode or not name or not verfallsdatum:
                return "🚫 Fehler: Alle Felder müssen ausgefüllt sein!"

            # 🔍 Überprüfen, ob der Barcode bereits in einer offenen Bestellung ist
            self.cursor.execute("SELECT COUNT(*) FROM bestellungen WHERE barcode = ? AND status = 'Offen'", (barcode,))
            offene_bestellung = self.cursor.fetchone()[0]

            if offene_bestellung > 0:
                return "🚫 Fehler: Dieser Barcode ist in einer offenen Bestellung und kann nicht erneut hinzugefügt werden!"

            # 🔍 Überprüfen, ob der Barcode bereits existiert
            self.cursor.execute("SELECT * FROM lagerbestand WHERE barcode = ?", (barcode,))
            row = self.cursor.fetchone()

            if row:
                return f"🚫 Fehler: Barcode {barcode} existiert bereits im Lager!"

            # 📅 Überprüfen des Datumsformats (YYYY-MM-DD)
            try:
                datetime.strptime(verfallsdatum, '%Y-%m-%d')
            except ValueError:
                return "⚠️ Fehler: Verfallsdatum muss im Format YYYY-MM-DD sein!"

            # ✅ Medikament hinzufügen
            self.cursor.execute(
                "INSERT INTO lagerbestand (barcode, name, menge, verfallsdatum, ort) VALUES (?, ?, 1, ?, ?)", 
                (barcode, name, verfallsdatum, ort)
            )
            self.db_conn.commit()

            # Aktion loggen
            self.datenbank.log_aktion(f"📦 Medikament hinzugefügt: {name} (Barcode: {barcode})")
            return f"✅ Erfolg: {name} hinzugefügt."
        
        except Exception as e:
            return f"🚫 Fehler: {str(e)}"



    def ware_entfernen(self, barcode):
        """Entfernt eine Ware nur, wenn sie im Lager ist. Medikamente im Automaten können nicht gelöscht werden."""
        try:
            # Überprüfen, ob der Barcode überhaupt eingegeben wurde
            if not barcode:
                print("\033[91m" + "🚫 Fehler: Barcode darf nicht leer sein!" + "\033[0m")
                return "🚫 Fehler: Barcode darf nicht leer sein!"
            
            # Überprüfen, ob das Medikament im Lager ist
            self.cursor.execute("SELECT ort FROM lagerbestand WHERE barcode = ?", (barcode,))
            row = self.cursor.fetchone()

            if row:
                ort = row[0]
                if ort == "Lager":
                    # Ware aus dem Lager entfernen
                    self.cursor.execute("DELETE FROM lagerbestand WHERE barcode = ?", (barcode,))
                    self.db_conn.commit()
                    print("\033[92m" + f"✅ Erfolg: Ware {barcode} aus dem Lager entfernt." + "\033[0m")
                    message = f"✅ Erfolg: Ware {barcode} aus dem Lager entfernt."
                else:
                    # Fehler, wenn sich die Ware im Automaten befindet
                    print("\033[91m" + f"🚫 Fehler: Ware {barcode} ist im Automaten und kann nicht gelöscht werden!" + "\033[0m")
                    message = f"🚫 Fehler: Ware {barcode} ist im Automaten und kann nicht gelöscht werden!"
            else:
                # Fehler, wenn der Barcode nicht im System gefunden wurde
                print("\033[91m" + f"🚫 Fehler: Barcode {barcode} nicht im Lagersystem gefunden!" + "\033[0m")
                message = f"🚫 Fehler: Barcode {barcode} nicht im Lagersystem gefunden!"

        except sqlite3.OperationalError:
            # Datenbank-Betriebsfehler (z. B. Verbindungsverlust)
            print("\033[91m" + "🚫 Fehler: Datenbank ist nicht verfügbar!" + "\033[0m")
            message = "🚫 Fehler: Datenbank ist nicht verfügbar!"

        except sqlite3.IntegrityError:
            # Datenbank-Integritätsfehler (z. B. Probleme mit Constraints)
            print("\033[91m" + "🚫 Fehler: Integritätsproblem in der Datenbank!" + "\033[0m")
            message = "🚫 Fehler: Integritätsproblem in der Datenbank!"

        except Exception as e:
            # Allgemeiner Fehlerfall
            print("\033[91m" + f"🚫 Unbekannter Fehler: {str(e)}" + "\033[0m")
            message = f"🚫 Unbekannter Fehler: {str(e)}"
        
        # Aktion protokollieren und Rückgabe der Nachricht
        self.datenbank.log_aktion(f"Ware entfernen: {message}")
        return message
    
    def get_artikel_anzahl(self):
        self.cursor.execute("SELECT name, SUM(menge) as total FROM lagerbestand GROUP BY name")
        data = self.cursor.fetchall()
        return pd.DataFrame(data, columns=["Name", "Menge"])  # Jetzt hat die Abfrage nur zwei Spalten
    
    def get_artikel_namen(self):
        self.cursor.execute("SELECT DISTINCT name FROM lagerbestand")
        data = self.cursor.fetchall()
        return [row[0] for row in data]  # Extrahiert nur die Namen in eine Liste
    
    def get_lagerbestand(self, barcode_filter=None, ort_filter=None):
        self.warnung._pruefe_warnungen()
        
        query = "SELECT barcode, name, menge, verfallsdatum, ort, kanal FROM lagerbestand WHERE 1=1"
        params = []

        if ort_filter in ["Lager", "Automat"]:
            query += " AND ort = ?"
            params.append(ort_filter)

        if barcode_filter:
            query += " AND barcode LIKE ?"
            params.append(f"%{barcode_filter}%")

        self.cursor.execute(query, params)
        data = self.cursor.fetchall()

        df = pd.DataFrame(data, columns=["Barcode", "Name", "Menge", "Verfallsdatum", "Ort", "Kanal"])
        return df