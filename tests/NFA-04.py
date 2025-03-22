import time
import pytest
import sys
import os

# src-Verzeichnis zum Pfad hinzufügen
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'lagersystem')))
from lager import Lager


lager = Lager()


@pytest.fixture
def test_wareneingang_erfolgreich():
    """Testet, ob eine neue Ware erfolgreich hinzugefügt wird."""
    barcode = "123456789012"
    name = "Aspirin"
    verfallsdatum = "2026-12-31"

    start_time = time.time()
    result = lager.ware_hinzufuegen(barcode, name, verfallsdatum, "Lager")
    duration = time.time() - start_time

    assert "✅ Erfolg" in result, f"Test fehlgeschlagen: {result}"
    assert (
        duration < 2
    ), f"Test fehlgeschlagen: Wareneingang dauerte {duration:.2f} Sekunden."


def test_wareneingang_doppelter_barcode():
    """Testet, ob ein doppelter Barcode erkannt wird."""
    barcode = "123456789012"
    name = "Aspirin"
    verfallsdatum = "2026-12-31"

    lager.ware_hinzufuegen(barcode, name, verfallsdatum, "Lager")
    result = lager.ware_hinzufuegen(barcode, name, verfallsdatum, "Lager")

    assert "existiert bereits" in result, "Doppelter Barcode wurde nicht erkannt!"


def test_wareneingang_ungueltiger_barcode():
    """Testet, ob ein ungültiger Barcode abgelehnt wird."""
    barcode = "abc123"
    name = "Ibuprofen"
    verfallsdatum = "2026-12-31"

    result = lager.ware_hinzufuegen(barcode, name, verfallsdatum, "Lager")
    assert "🚫 Fehler" in result, "Ungültiger Barcode wurde nicht erkannt!"


def test_wareneingang_abgelaufenes_medikament():
    """Testet, ob ein abgelaufenes Medikament abgelehnt wird."""
    barcode = "987654321098"
    name = "Paracetamol"
    verfallsdatum = "2022-01-01"

    result = lager.ware_hinzufuegen(barcode, name, verfallsdatum, "Lager")
    assert "⚠️ Fehler" in result, "Abgelaufenes Medikament wurde nicht erkannt!"


if __name__ == "__main__":
    pytest.main()
