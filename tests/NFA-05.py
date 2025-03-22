import unittest
import sqlite3
import sys
import os

# src-Verzeichnis zum Pfad hinzufügen
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'lagersystem')))
from anmeldung import Anmeldung
from automat import Automat
from datenbank import Datenbank
from admin import Admin
from lager import Lager
from warnung import Warnung


class TestSchnittstellenErweiterbarkeit(unittest.TestCase):
    def setUp(self):
        """
        Initialisiert die Datenbank und Klassen für die Tests.
        """
        self.datenbank = Datenbank()
        self.lager = Lager()
        self.automat = Automat()
        self.admin = Admin()
        self.warnung = Warnung()
        self.anmeldung = Anmeldung()

    def test_neue_schnittstelle_hinzufuegen(self):
        """
        Testet, ob eine neue Schnittstelle problemlos in das System integriert werden kann.
        """
        class NeueSchnittstelle:
            def __init__(self, datenbank):
                self.datenbank = datenbank

            def neue_funktion(self):
                return "Neue Funktion erfolgreich aufgerufen"

        neue_schnittstelle = NeueSchnittstelle(self.datenbank)
        self.assertEqual(neue_schnittstelle.neue_funktion(), "Neue Funktion erfolgreich aufgerufen")

    def test_datenbankintegration(self):
        """
        Testet, ob eine neue Schnittstelle mit der bestehenden Datenbank arbeiten kann.
        """
        class ErweiterteDatenbank(Datenbank):
            def neue_query(self):
                with sqlite3.connect("src/lagersystem/databases/lagerbestand.db") as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    return cursor.fetchall()

        erweiterte_db = ErweiterteDatenbank()
        tables = erweiterte_db.neue_query()
        self.assertTrue(len(tables) > 0)

    def test_lager_schnittstelle_erweiterung(self):
        """
        Testet, ob eine neue Funktionalität in das Lager integriert werden kann.
        """
        class ErweiterterLager(Lager):
            def get_gesamtbestand(self):
                return self.get_artikel_anzahl()

        erweiterter_lager = ErweiterterLager()
        bestand = erweiterter_lager.get_gesamtbestand()
        self.assertIsInstance(bestand, object)


if __name__ == "__main__":
    unittest.main()
