import pandas as pd
import sqlite3
from datetime import datetime
from warnung import Warnung  # Ensure you import the Warnung class
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
        self.db_conn = sqlite3.connect('lagerbestand.db', check_same_thread=False)
        self.cursor = self.db_conn.cursor()
        self.warnung = Warnung()  # Instantiate Warnung to access its methods
        self.datenbank = Datenbank()

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
        try:
            if not barcode or not name or not verfallsdatum:
                return "🚫 Fehler: Alle Felder müssen ausgefüllt sein!"

            # Prüfen, ob der Barcode bereits in einer offenen Bestellung ist
            self.cursor.execute("SELECT COUNT(*) FROM bestellungen WHERE barcode = ? AND status = 'Offen'", (barcode,))
            offene_bestellung = self.cursor.fetchone()[0]

            if offene_bestellung > 0:
                return "🚫 Fehler: Dieser Barcode ist in einer offenen Bestellung und kann nicht erneut hinzugefügt werden!"

            # Prüfen, ob der Barcode bereits existiert
            self.cursor.execute("SELECT * FROM lagerbestand WHERE barcode = ?", (barcode,))
            row = self.cursor.fetchone()

            if row:
                return f"🚫 Fehler: Barcode {barcode} existiert bereits im Lager!"

            # Überprüfung des Datumsformats
            try:
                datetime.strptime(verfallsdatum, '%Y-%m-%d')
            except ValueError:
                return "⚠️ Fehler: Verfallsdatum muss im Format YYYY-MM-DD sein!"

            # Medikament hinzufügen
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
        """
        Entfernt eine Ware aus dem Lagerbestand, falls sie nicht in einem Automaten gespeichert ist.

        :param barcode: Der Barcode der zu entfernenden Ware
        :return: Eine Erfolgsmeldung oder eine Fehlermeldung
        """
        try:
            if not barcode:
                return "🚫 Fehler: Barcode darf nicht leer sein!"
            
            # Überprüfen, ob das Medikament im Lager ist
            self.cursor.execute("SELECT ort FROM lagerbestand WHERE barcode = ?", (barcode,))
            row = self.cursor.fetchone()

            if row:
                ort = row[0]
                if ort == "Lager":
                    self.cursor.execute("DELETE FROM lagerbestand WHERE barcode = ?", (barcode,))
                    self.db_conn.commit()
                    message = f"✅ Erfolg: Ware {barcode} aus dem Lager entfernt."
                else:
                    message = f"🚫 Fehler: Ware {barcode} ist im Automaten und kann nicht gelöscht werden!"
            else:
                message = f"🚫 Fehler: Barcode {barcode} nicht im Lagersystem gefunden!"
        except sqlite3.OperationalError:
            message = "🚫 Fehler: Datenbank ist nicht verfügbar!"
        except sqlite3.IntegrityError:
            message = "🚫 Fehler: Integritätsproblem in der Datenbank!"
        except Exception as e:
            message = f"🚫 Unbekannter Fehler: {str(e)}"
        
        self.datenbank.log_aktion(f"Ware entfernen: {message}")
        return message
    
    def get_artikel_anzahl(self):
        """
        Gibt eine DataFrame mit der Anzahl der vorhandenen Artikel zurück.

        :return: Pandas DataFrame mit den Spalten Name und Menge
        """
        self.cursor.execute("SELECT name, SUM(menge) as total FROM lagerbestand GROUP BY name")
        data = self.cursor.fetchall()
        return pd.DataFrame(data, columns=["Name", "Menge"])
    
    def get_artikel_namen(self):
        """
        Gibt eine Liste mit den Namen aller im Lager vorhandenen Artikel zurück.

        :return: Liste mit Artikelnamen
        """
        self.cursor.execute("SELECT DISTINCT name FROM lagerbestand")
        data = self.cursor.fetchall()
        return [row[0] for row in data]
    
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
            query += " AND barcode LIKE ?"
            params.append(f"%{barcode_filter}%")

        self.cursor.execute(query, params)
        data = self.cursor.fetchall()

        df = pd.DataFrame(data, columns=["Barcode", "Name", "Menge", "Verfallsdatum", "Ort", "Kanal"])
        return df
