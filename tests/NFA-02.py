import os
import time
import sqlite3
import requests
from locust import HttpUser, task, between

# === Dynamischer Pfad zur Datenbank ===
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'src', 'lagersystem'))
DB_PATH = os.path.join(BASE_DIR, 'databases', 'lagerbestand.db')


class PerformanceTestUser(HttpUser):
    wait_time = between(1, 3)  # Simuliert reale Benutzer mit zufälligen Wartezeiten

    @task
    def login_test(self):
        """
        Testet die Reaktionszeit der Benutzeranmeldung.
        """
        start_time = time.time()
        response = self.client.post(
            "/api/login", json={"username": "testuser", "password": "testpass"}
        )
        end_time = time.time()

        reaktionszeit = (end_time - start_time) * 1000
        print(f"Login-Antwortzeit: {reaktionszeit:.2f} ms")

        if response.status_code == 200:
            print("✅ Anmeldung erfolgreich!")
        else:
            print("❌ Anmeldung fehlgeschlagen!")

    @task
    def get_lagerbestand(self):
        """
        Testet die Reaktionszeit für das Abrufen des Lagerbestands.
        """
        start_time = time.time()
        response = self.client.get("/api/lagerbestand")
        end_time = time.time()

        reaktionszeit = (end_time - start_time) * 1000
        print(f"Lagerbestand-Antwortzeit: {reaktionszeit:.2f} ms")

    @task
    def bestellung_abschicken(self):
        """
        Testet die Reaktionszeit für das Abschicken einer Bestellung.
        """
        start_time = time.time()
        response = self.client.post(
            "/api/bestellung", json={"kundennummer": "12345678", "barcode": "87654321"}
        )
        end_time = time.time()

        reaktionszeit = (end_time - start_time) * 1000
        print(f"Bestellung-Antwortzeit: {reaktionszeit:.2f} ms")


def test_reaktionszeit(db_path=DB_PATH, iterations=5):
    """
    Testet die Reaktionszeit des Systems für Datenbankoperationen über mehrere Durchläufe.
    Die Reaktionszeit sollte unter 500 Millisekunden bleiben.
    """
    ergebnisse = []

    for i in range(iterations):
        start_time = time.time()

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Test 1: Anzahl der Einträge abrufen
            cursor.execute("SELECT COUNT(*) FROM lagerbestand")
            _ = cursor.fetchone()

            # Test 2: Zufälligen Eintrag abrufen
            cursor.execute("SELECT * FROM lagerbestand ORDER BY RANDOM() LIMIT 1")
            _ = cursor.fetchone()

            # Test 3: Dummy-Eintrag (zurückrollen)
            cursor.execute("""
                INSERT INTO lagerbestand (barcode, name, menge, verfallsdatum, ort)
                VALUES ('12345678', 'TestMedikament', 1, '2099-12-31', 'Lager')
            """)
            conn.rollback()

            conn.close()
        except Exception as e:
            print(f"❌ Fehler bei der Datenbankabfrage: {e}")
            return False

        end_time = time.time()
        reaktionszeit = (end_time - start_time) * 1000
        ergebnisse.append(reaktionszeit)
        print(f"Durchlauf {i+1}: Reaktionszeit = {reaktionszeit:.2f} ms")

    durchschnitt = sum(ergebnisse) / iterations
    print(f"⏱ Durchschnittliche Reaktionszeit: {durchschnitt:.2f} ms")

    return durchschnitt < 500


# Test ausführen
if __name__ == "__main__":
    erfolg = test_reaktionszeit()
    if erfolg:
        print("✅ System reagiert innerhalb des akzeptablen Zeitlimits.")
    else:
        print("⚠️ Systemreaktionszeit überschreitet 500 ms!")
