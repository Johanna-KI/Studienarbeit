import sqlite3
import bcrypt
import random


class Anmeldung:
    """
    Diese Klasse verwaltet die Benutzerregistrierung und Authentifizierung.
    """
    def hash_password(self, password):
        """
        Hashing des Passworts mit bcrypt.
        
        :param password: Klartext-Passwort.
        :return: Gehashter Passwort-String.
        """
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def verify_password(self, password, hashed):
        """
        Überprüfung eines Passworts gegen einen gespeicherten Hash.
        
        :param password: Klartext-Passwort.
        :param hashed: Gespeicherter Hash-Wert.
        :return: True, wenn das Passwort übereinstimmt, sonst False.
        """
        return bcrypt.checkpw(password.encode(), hashed.encode())

    def generate_kundennummer(self):
        """
        Generiert eine zufällige achtstellige Kundennummer.
        
        :return: Zufällige Kundennummer als String.
        """
        return str(random.randint(10000000, 99999999))

    def register_user(self, username, password, role="user"):
        """
        Registriert einen neuen Benutzer und speichert ihn in der Datenbank.
        
        :param username: Benutzername.
        :param password: Passwort im Klartext.
        :param role: Benutzerrolle, standardmäßig "user".
        :return: Tuple (Kundennummer, Rolle) bei Erfolg, sonst Fehlermeldung.
        """
        with sqlite3.connect('users.db') as conn:
            cursor = conn.cursor()

            # 1️⃣ Überprüfen, ob der Benutzername bereits existiert
            cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (username,))
            if cursor.fetchone()[0] > 0:
                return None, "🚫 Fehler: Benutzername bereits vergeben! Bitte wählen Sie einen anderen."

            # 2️⃣ Überprüfen, ob bereits ein Admin existiert
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
            admin_exists = cursor.fetchone()[0] > 0

            if not admin_exists:
                role = "admin"  # Der erste Benutzer wird automatisch Admin

            # 3️⃣ Sicherstellen, dass die generierte Kundennummer einzigartig ist
            while True:
                kundennummer = str(random.randint(10000000, 99999999))
                cursor.execute("SELECT COUNT(*) FROM users WHERE kundennummer = ?", (kundennummer,))
                if cursor.fetchone()[0] == 0:
                    break  # Eindeutige Kundennummer gefunden

            hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

            try:
                cursor.execute("INSERT INTO users (kundennummer, username, password_hash, role) VALUES (?, ?, ?, ?)",
                            (kundennummer, username, hashed_pw, role))
                conn.commit()
                return kundennummer, role  # ✅ Erfolgreiche Registrierung
            except sqlite3.IntegrityError:
                return None, "🚫 Fehler: Registrierung fehlgeschlagen!"
            
    def get_user(self, username):
        """
        Ruft die Benutzerinformationen aus der Datenbank ab.
        
        :param username: Benutzername.
        :return: Tuple (Kundennummer, Passwort-Hash, Rolle) oder None, falls der Benutzer nicht existiert.
        """
        with sqlite3.connect('users.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT kundennummer, password_hash, role FROM users WHERE username = ?", (username,))
            return cursor.fetchone()
