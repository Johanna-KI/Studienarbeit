import pytest
import sqlite3
import sys
import os

# src-Verzeichnis zum Pfad hinzufügen
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'lagersystem')))
from lager import Lager


@pytest.fixture
def test_lager():
    """Erstellt eine Testinstanz des Lagers mit einer In-Memory-Datenbank"""
    lager = Lager()
    lager.db_conn = sqlite3.connect(":memory:")  # Temporäre Test-Datenbank
    lager.cursor = lager.db_conn.cursor()

    # ✅ Tabellen für den Test erstellen
    lager.cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS lagerbestand (
            barcode TEXT PRIMARY KEY,
            name TEXT,
            menge INTEGER,
            verfallsdatum TEXT,
            ort TEXT DEFAULT 'Lager'
        )
    """
    )

    lager.cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS bestellungen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bestellgruppe_id INTEGER,
            kundennummer TEXT,
            barcode TEXT,
            name TEXT,
            bestelldatum TEXT,
            status TEXT DEFAULT 'Offen'
        )
    """
    )

    lager.db_conn.commit()  # 🔥 Datenbank-Transaktionen speichern
    return lager


def test_wareneingang(test_lager):
    """Testet, ob der Wareneingang korrekt erfasst wird"""
    result = test_lager.ware_hinzufuegen("1234567890", "TestMedikament", "2026-12-31")
    print(f"DEBUG Wareneingang: {result}")  # 🛠 Debugging

    assert "Erfolg" in result

    # Überprüfung in der Datenbank
    test_lager.cursor.execute(
        "SELECT menge FROM lagerbestand WHERE barcode = '1234567890'"
    )
    menge = test_lager.cursor.fetchone()
    print(f"DEBUG Datenbank Wareneingang: {menge}")  # 🛠 Debugging
    assert menge is not None and menge[0] == 1  # Der Bestand sollte 1 sein


def test_warenausgang(test_lager):
    """Testet, ob der Warenausgang korrekt verarbeitet wird"""
    test_lager.ware_hinzufuegen("1234567890", "TestMedikament", "2026-12-31")
    result = test_lager.ware_entfernen("1234567890")
    print(f"DEBUG Warenausgang: {result}")  # 🛠 Debugging

    assert "Erfolg" in result

    # Überprüfung in der Datenbank
    test_lager.cursor.execute(
        "SELECT COUNT(*) FROM lagerbestand WHERE barcode = '1234567890'"
    )
    count = test_lager.cursor.fetchone()[0]
    print(f"DEBUG Datenbank Warenausgang: {count}")  # 🛠 Debugging
    assert count == 0  # Ware sollte entfernt sein


def test_bestandsabgleich(test_lager):
    """Prüft, ob der Lagerbestand mit der Erwartung übereinstimmt"""
    test_lager.ware_hinzufuegen("1234567890", "TestMedikament", "2026-12-31")
    test_lager.ware_hinzufuegen("0987654321", "TestMedikament2", "2025-12-31")

    bestand = test_lager.get_artikel_anzahl()
    print(f"DEBUG Bestandsabgleich: {bestand}")  # 🛠 Debugging

    assert bestand.shape[0] == 2  # Es sollten 2 Artikel im Lager sein


def test_fehlbestandsrate(test_lager):
    """Prüft, ob die Fehlbestandsrate unter 2% bleibt"""

    # 🔹 98 korrekte Artikel einfügen
    for i in range(98):
        test_lager.ware_hinzufuegen(
            str(1000000000 + i), f"TestMedikament_{i}", "2026-12-31"
        )

    # 🔹 **Fehlbestände automatisch zählen**
    test_lager.cursor.execute(
        "SELECT COUNT(*) FROM lagerbestand WHERE barcode = '' OR menge <= 0 OR verfallsdatum IS NULL"
    )
    fehlbestand = test_lager.cursor.fetchone()[0]

    # 🔹 Gesamtartikel zählen
    bestand = test_lager.get_artikel_anzahl()
    gesamt_artikel = bestand["Menge"].sum()

    # 🔹 Fehlbestandsrate berechnen
    fehlbestandsrate = (fehlbestand / gesamt_artikel) * 100 if gesamt_artikel > 0 else 0

    print(f"🔍 Automatische Fehlbestandsrate: {fehlbestandsrate:.2f}%")

    assert (
        fehlbestandsrate < 2.0
    ), f"⚠️ Fehlbestandsrate zu hoch! ({fehlbestandsrate:.2f}%)"
