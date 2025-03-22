import random
import sys
import os

# src-Verzeichnis zum Pfad hinzufügen
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'lagersystem')))

from lager import Lager

# 1️⃣ Test-Datenbank mit neuen Barcodes erstellen
lager = Lager()

# Liste mit 90 zufälligen gültigen Barcodes (noch nicht in der DB)
valid_barcodes = [str(random.randint(1000000000, 9999999999)) for _ in range(90)]

# Liste mit 10 ungültigen Barcodes (zu kurz, nicht numerisch, leer)
invalid_barcodes = ["", "ABCDEF1234", "12345", "0000000000", "abcdefghij"] * 2

# Testliste mischen
test_barcodes = valid_barcodes + invalid_barcodes
random.shuffle(test_barcodes)

erfolgreich = 0
gesamt = len(test_barcodes)
fehler_log = []

# 2️⃣ Testlauf: Barcodes hinzufügen und Erfolg überprüfen
for barcode in test_barcodes:
    result = lager.ware_hinzufuegen(barcode, "TestMedikament", "2026-12-31")

    if "Erfolg" in result:  # Erfolgsmeldung vorhanden?
        erfolgreich += 1
    else:
        fehler_log.append((barcode, result))  # Fehler speichern

# 3️⃣ Genauigkeitsberechnung
genauigkeit = (erfolgreich / gesamt) * 100
print(f"\n✅ **Genauigkeit:** {genauigkeit:.2f}%\n")

# 4️⃣ Fehler ausgeben
print("\n🚨 Fehlerprotokoll 🚨")
for barcode, fehler in fehler_log:
    print(f"Barcode: {barcode} → Fehler: {fehler}")

# 5️⃣ Testbedingung für Ziel-Genauigkeit
assert genauigkeit >= 90, f"Genauigkeitsrate zu niedrig: {genauigkeit:.2f}%"
