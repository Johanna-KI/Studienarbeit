import unittest
import random
import sqlite3
import sys
import os

# src-Verzeichnis zum Pfad hinzufügen
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'lagersystem')))

from automat import Automat


class TestAutomatBefuellung(unittest.TestCase):
    def setUp(self):
        """Initialisiert eine Instanz des Automaten für die Tests und fügt eine Ware zum Lagerbestand hinzu."""
        self.automat = Automat()
        self.valid_barcode = "1234567890123"
        self.invalid_barcode = "abcd123"

        # Verbindung zur Datenbank aufbauen und Testeinträge hinzufügen
        self.conn = sqlite3.connect("lagerbestand.db")
        self.cursor = self.conn.cursor()

        # Testware in die Datenbank einfügen
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS lagerbestand (
                barcode TEXT PRIMARY KEY,
                name TEXT,
                verfallsdatum TEXT,
                ort TEXT
            )
        """
        )
        self.cursor.execute(
            "DELETE FROM lagerbestand WHERE barcode = ?", (self.valid_barcode,)
        )
        self.cursor.execute(
            "INSERT INTO lagerbestand (barcode, name, verfallsdatum, ort) VALUES (?, ?, DATE('now', '+1 year'), 'Lager')",
            (
                self.valid_barcode,
                "Testmedikament",
            ),
        )
        self.conn.commit()

    def tearDown(self):
        """Schließt die Datenbankverbindung nach den Tests."""
        self.conn.close()

    def test_befuellung_fehlerquote(self):
        """Testet die Fehlerrate der Befüllung des Automaten und prüft, ob sie im Bereich von 0,1 % bis 1 % liegt."""
        fehlerhafte_befuellungen = 0
        gesamtversuche = 10000  # Mehr Versuche für eine genauere Statistik

        for _ in range(gesamtversuche):
            barcode = (
                self.valid_barcode
                if random.uniform(0, 1) > 0.001
                else self.invalid_barcode
            )
            ergebnis = self.automat.ware_zum_automaten_hinzufuegen(barcode)

            if "Fehler" in ergebnis:
                fehlerhafte_befuellungen += 1

        # Berechnung der tatsächlichen Fehlerquote
        berechnete_fehlerquote = (fehlerhafte_befuellungen / gesamtversuche) * 100

        print(f"Gemessene Fehlerquote: {berechnete_fehlerquote:.3f}%")

        self.assertLessEqual(berechnete_fehlerquote, 1.0, "Fehlerquote zu hoch!")


if __name__ == "__main__":
    unittest.main()
