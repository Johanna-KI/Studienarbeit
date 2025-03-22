import pandas as pd
import sqlite3
import re
import os
from datetime import datetime
from warnung import Warnung  
from datenbank import Datenbank

class Lager:
    """
    Diese Klasse verwaltet den Lagerbestand eines Unternehmens.
    Sie ermöglicht das Hinzufügen, Entfernen und Abfragen von Waren.
    """
    
    def __init__(self):
        """
        Initialisiert die Lagerklasse mit einer Verbindung zur SQLite-Datenbank,
        einer Warnungsinstanz und einer Datenbankinstanz.
        """
        base_dir = os.path.dirname(__file__)  # src/lagersystem
        db_path = os.path.join(base_dir, 'databases', 'lagerbestand.db')

        # Verbindung herstellen
        self.db_conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.db_conn.cursor()
        self.warnung = Warnung()
        self.datenbank = Datenbank()

    def ist_gueltiger_barcode(self, barcode):
        """
        Überprüft, ob ein Barcode gültig ist (numerisch, mindestens 8 und maximal 13 Zeichen lang).
        :param barcode: Der zu überprüfende Barcode
        :return: True, wenn gültig, sonst False
        """
        return bool(re.fullmatch(r'\d{8,13}', str(barcode)))

    def _ist_barcode_in_bestellung(self, barcode):
        """Überprüft, ob der Barcode in einer offenen Bestellung ist."""
        self.cursor.execute("SELECT COUNT(*) FROM bestellungen WHERE barcode = ? AND status = 'Offen'", (barcode,))
        return self.cursor.fetchone()[0] > 0

    def _ist_barcode_im_lager(self, barcode):
        """Überprüft, ob ein Barcode bereits im Lager existiert."""
        self.cursor.execute("SELECT COUNT(*) FROM lagerbestand WHERE barcode = ?", (barcode,))
        return self.cursor.fetchone()[0] > 0

    def _ist_verfallsdatum_gueltig(self, verfallsdatum):
        """Überprüft, ob das Verfallsdatum im richtigen Format ist und nicht abgelaufen ist."""
        try:
            datum = datetime.strptime(verfallsdatum, '%Y-%m-%d')
            return datum >= datetime.today()
        except ValueError:
            return False

    def ware_hinzufuegen(self, barcode, name, verfallsdatum, ort='Lager'):
        """
        Fügt eine Ware zum Lagerbestand hinzu, falls sie nicht bereits existiert und
        nicht in einer offenen Bestellung enthalten ist.

        :param barcode: Der eindeutige Barcode des Produkts
        :param name: Name des Produkts
        :param verfallsdatum: Ablaufdatum im Format 'YYYY-MM-DD'
        :param ort: Lagerort (Standard: 'Lager')
        :return: Eine Erfolgsmeldung oder eine Fehlermeldung
        """
        if not all([barcode, name, verfallsdatum]):
            return "🚫 Fehler: Alle Felder müssen ausgefüllt sein!"
        if not self.ist_gueltiger_barcode(barcode):
            return "🚫 Fehler: Ungültiger Barcode! Er muss 8-13 Ziffern enthalten."
        if self._ist_barcode_in_bestellung(barcode):
            return "🚫 Fehler: Dieser Barcode ist in einer offenen Bestellung!"
        if self._ist_barcode_im_lager(barcode):
            return f"🚫 Fehler: Barcode {barcode} existiert bereits im Lager!"
        if not self._ist_verfallsdatum_gueltig(verfallsdatum):
            return "⚠️ Fehler: Verfallsdatum ungültig oder Ware ist abgelaufen!"

        try:
            self.cursor.execute(
                "INSERT INTO lagerbestand (barcode, name, menge, verfallsdatum, ort) VALUES (?, ?, 1, ?, ?)", 
                (barcode, name, verfallsdatum, ort)
            )
            self.db_conn.commit()
            self.datenbank.log_aktion(f"📦 Medikament hinzugefügt: {name} (Barcode: {barcode})")
            return f"✅ Erfolg: {name} hinzugefügt."
        except sqlite3.Error as e:
            return f"🚫 Fehler bei der Datenbank: {str(e)}"

    def ware_entfernen(self, barcode):
        """
        Entfernt eine Ware aus dem Lagerbestand, falls sie nicht in einem Automaten gespeichert ist.

        :param barcode: Der Barcode der zu entfernenden Ware
        :return: Eine Erfolgsmeldung oder eine Fehlermeldung
        """
        if not barcode or not self.ist_gueltiger_barcode(barcode):
            return "🚫 Fehler: Ungültiger oder leerer Barcode!"

        try:
            self.cursor.execute("SELECT ort FROM lagerbestand WHERE barcode = ?", (barcode,))
            row = self.cursor.fetchone()
            if not row:
                return f"🚫 Fehler: Barcode {barcode} nicht im Lager gefunden!"

            if row[0] == "Automat":
                return f"🚫 Fehler: Ware {barcode} ist im Automaten und kann nicht gelöscht werden!"

            self.cursor.execute("DELETE FROM lagerbestand WHERE barcode = ?", (barcode,))
            self.db_conn.commit()
            self.datenbank.log_aktion(f"✅ Ware {barcode} entfernt.")
            return f"✅ Erfolg: Ware {barcode} entfernt."
        except sqlite3.Error as e:
            return f"🚫 Fehler bei der Datenbank: {str(e)}"

    def get_artikel_anzahl(self):
        """Gibt eine DataFrame mit der Anzahl der vorhandenen Artikel zurück."""
        self.cursor.execute("SELECT name, SUM(menge) as total FROM lagerbestand GROUP BY name")
        data = self.cursor.fetchall()
        return pd.DataFrame(data, columns=["Name", "Menge"])

    def get_artikel_namen(self):
        """Gibt eine Liste mit den Namen aller im Lager vorhandenen Artikel zurück."""
        self.cursor.execute("SELECT DISTINCT name FROM lagerbestand")
        return [row[0] for row in self.cursor.fetchall()]

    def get_lagerbestand(self, barcode_filter=None, ort_filter=None):
        """
        Ruft den aktuellen Lagerbestand ab, mit optionalen Filtern für Barcode und Ort.

        :param barcode_filter: Optionaler Filter für Barcode (Substring-Suche)
        :param ort_filter: Optionaler Filter für Lagerort ('Lager' oder 'Automat')
        :return: Pandas DataFrame mit den Lagerdaten
        """
        self.warnung._pruefe_warnungen()

        query = "SELECT barcode, name, menge, verfallsdatum, ort, kanal FROM lagerbestand WHERE 1=1"
        params = []

        if ort_filter in ["Lager", "Automat"]:
            query += " AND ort = ?"
            params.append(ort_filter)

        if barcode_filter:
            if not self.ist_gueltiger_barcode(barcode_filter):
                return "🚫 Fehler: Ungültiger Barcode-Filter!"
            query += " AND barcode LIKE ?"
            params.append(f"%{barcode_filter}%")

        self.cursor.execute(query, params)
        return pd.DataFrame(self.cursor.fetchall(), columns=["Barcode", "Name", "Menge", "Verfallsdatum", "Ort", "Kanal"])
