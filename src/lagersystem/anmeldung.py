import os
import sqlite3
import bcrypt
import random


class Anmeldung:
    """
    Diese Klasse verwaltet die Benutzerregistrierung und Authentifizierung.
    """

    def __init__(self):
        """
        Konstruktor, der den Datenbankpfad korrekt relativ zum Dateispeicherort setzt.
        """
        base_dir = os.path.dirname(__file__)  # src/lagersystem
        self.db_path = os.path.join(base_dir, 'databases', 'users.db')

    def connect_db(self):
        """Erstellt eine Verbindung zur SQLite-Datenbank."""
        return sqlite3.connect(self.db_path)

    def hash_password(self, password):
        """Hashing des Passworts mit bcrypt."""
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def verify_password(self, password, hashed):
        """Überprüfung eines Passworts gegen einen gespeicherten Hash."""
        return bcrypt.checkpw(password.encode(), hashed.encode())

    def generate_kundennummer(self):
        """Generiert eine zufällige achtstellige Kundennummer."""
        return str(random.randint(10000000, 99999999))

    def register_user(self, username, password, role="user"):
        """
        Registriert einen neuen Benutzer in der Datenbank.
        """
        with self.connect_db() as conn:
            cursor = conn.cursor()

            # Benutzername prüfen
            cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,))
            if cursor.fetchone()[0] > 0:
                return None, "🚫 Fehler: Benutzername bereits vergeben! Bitte wählen Sie einen anderen."

            # Admin automatisch setzen, wenn keiner existiert
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
            if cursor.fetchone()[0] == 0:
                role = "admin"

            # Einzigartige Kundennummer generieren
            while True:
                kundennummer = self.generate_kundennummer()
                cursor.execute("SELECT COUNT(*) FROM users WHERE kundennummer = ?", (kundennummer,))
                if cursor.fetchone()[0] == 0:
                    break

            hashed_pw = self.hash_password(password)

            try:
                cursor.execute(
                    "INSERT INTO users (kundennummer, username, password_hash, role) VALUES (?, ?, ?, ?)",
                    (kundennummer, username, hashed_pw, role)
                )
                conn.commit()
                return kundennummer, role
            except sqlite3.IntegrityError:
                return None, "🚫 Fehler: Registrierung fehlgeschlagen!"

    def get_user(self, username):
        """
        Ruft die Benutzerinformationen aus der Datenbank ab.
        """
        with self.connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT kundennummer, password_hash, role FROM users WHERE username = ?",
                (username,)
            )
            return cursor.fetchone()

    def loesche_user(self, username):
        """Löscht einen Benutzer aus der Datenbank, falls vorhanden."""
        with self.connect_db() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE username = ?", (username,))
            conn.commit()
