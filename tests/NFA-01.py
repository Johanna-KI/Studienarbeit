import os
import pandas as pd
import pytest
from datetime import datetime

# === Konfiguration ===

# Dynamischer Pfad zur Logdatei relativ zum aktuellen Dateipfad (tests/)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'lagersystem'))
LOG_DATEI = os.path.join(BASE_DIR, 'logs', 'log_protokoll.csv')

KRITISCHE_KEYWORDS = [
    "App-Absturz", "Systemfehler", "Datenbankfehler", "nicht reagiert",
    "Timeout", "unbehandelte Ausnahme", "500", "kritischer Fehler"
]

MTBF_MINDESTWERT = 1000  # in Stunden (laut Anforderung)


def lade_log():
    assert os.path.exists(LOG_DATEI), f"❌ Logdatei nicht gefunden unter Pfad: {LOG_DATEI}"
    df = pd.read_csv(LOG_DATEI, names=["Zeitstempel", "Kundennummer", "Aktion"])
    df["Zeitstempel"] = pd.to_datetime(df["Zeitstempel"], errors="coerce")
    df = df.dropna(subset=["Zeitstempel"])
    return df


def berechne_mtbf(df: pd.DataFrame) -> float:
    kritische_fehler = df[df["Aktion"].str.contains('|'.join(KRITISCHE_KEYWORDS), case=False, na=False)].copy()
    kritische_fehler = kritische_fehler.sort_values("Zeitstempel")
    kritische_fehler["Delta"] = kritische_fehler["Zeitstempel"].diff().dt.total_seconds() / 3600
    return kritische_fehler["Delta"].mean() if len(kritische_fehler) > 1 else None


# === Pytest-Testfall ===
def test_mtbf_stabilitaet():
    """
    Testet, ob der MTBF-Wert innerhalb des gewünschten Bereichs liegt.
    """
    df = lade_log()
    mtbf = berechne_mtbf(df)

    if mtbf is None:
        pytest.skip("Nicht genügend kritische Fehler für MTBF-Berechnung.")

    print(f"⏱ Berechneter MTBF: {mtbf:.2f} Stunden")
    assert mtbf >= MTBF_MINDESTWERT, f"❌ MTBF liegt unter {MTBF_MINDESTWERT} Stunden! Aktuell: {mtbf:.2f} h"
