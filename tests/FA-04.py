import unittest
import sqlite3
from datetime import datetime, timedelta
import sys
import os

# src-Verzeichnis zum Pfad hinzufügen
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'lagersystem')))
from datenbank import Datenbank
from automat import Automat
from lager import Lager

class TestBestellungsZuverlaessigkeit(unittest.TestCase):
    """
    Integrationstest zur Überprüfung, ob mindestens 95 % der realen Bestellvorgänge korrekt verarbeitet werden.
    Dabei wird überprüft, ob der Lagerbestand korrekt gelöscht wurde.
    """

    @classmethod
    def setUpClass(cls):
        cls.datenbank = Datenbank()
        cls.automat = Automat()
        cls.lager = Lager()
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'lagersystem'))
        db_path = os.path.join(base_dir, 'databases', 'lagerbestand.db')
        cls.conn = sqlite3.connect(db_path)
        cls.cursor = cls.conn.cursor()
        cls.kundennummer = "99999999"

        cls.erfolg_counter = 0
        cls.testdurchläufe = 100

        # Vorbereitungen: 100 Medikamente ins Lager einfügen
        heute = datetime.today()
        for i in range(cls.testdurchläufe):
            barcode = f"900000{i:03d}"  # z. B. 900000000, 900000001, ...
            name = f"TestMedikament{i}"
            verfallsdatum = (heute + timedelta(days=365)).strftime("%Y-%m-%d")
            cls.cursor.execute(
                "INSERT INTO lagerbestand (barcode, name, menge, verfallsdatum, ort) VALUES (?, ?, 1, ?, 'Lager')",
                (barcode, name, verfallsdatum)
            )
        cls.conn.commit()

    def test_bestellungen_zu_95_prozent_erfolgreich(self):
        """Testet, ob mindestens 95 % der realen Bestellvorgänge korrekt abgeschlossen und gelöscht werden."""
        for i in range(self.testdurchläufe):
            barcode = f"900000{i:03d}"

            # Medikament in den Automaten verschieben
            msg1 = self.automat.ware_zum_automaten_hinzufuegen(barcode)
            # In den Warenkorb legen
            msg2 = self.automat.ware_zum_warenkorb_hinzufuegen(barcode)
            # Bestellung abschicken
            result = self.automat.bestellung_abschicken(self.kundennummer)

            # Überprüfen, ob der Datensatz gelöscht wurde
            self.cursor.execute("SELECT * FROM lagerbestand WHERE barcode = ?", (barcode,))
            eintrag = self.cursor.fetchone()

            if eintrag is None:
                self.erfolg_counter += 1
            else:
                print(f"❌ Datensatz nicht gelöscht für Barcode {barcode} – Fehler beim Bestellvorgang")

        print(f"✅ Erfolgreiche Bestellungen: {self.erfolg_counter} von {self.testdurchläufe}")
        self.assertGreaterEqual(
            self.erfolg_counter,
            int(self.testdurchläufe * 0.95),
            f"Nur {self.erfolg_counter} von {self.testdurchläufe} Bestellungen wurden korrekt verarbeitet. Erwartet: mindestens 95 %."
        )

    @classmethod
    def tearDownClass(cls):
        """Bereinigt die Testdaten nach dem Test."""
        cls.cursor.execute("DELETE FROM lagerbestand WHERE barcode LIKE '900000%'")
        cls.cursor.execute("DELETE FROM bestellungen WHERE barcode LIKE '900000%'")
        cls.conn.commit()
        cls.conn.close()


if __name__ == "__main__":
    unittest.main()
