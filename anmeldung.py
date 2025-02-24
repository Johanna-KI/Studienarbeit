import streamlit as st
import pandas as pd
import sqlite3
import bcrypt
import time
import csv
import random
from datetime import datetime

class Anmeldung:
    def hash_password(self, password):
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def verify_password(self, password, hashed):
        return bcrypt.checkpw(password.encode(), hashed.encode())

    def generate_kundennummer(self):
        return str(random.randint(10000000, 99999999))

    def register_user(self, username, password, role="user"):
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
        with sqlite3.connect('users.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT kundennummer, password_hash, role FROM users WHERE username = ?", (username,))
            return cursor.fetchone()