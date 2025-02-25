import streamlit as st
import sqlite3
import time
import csv
from datetime import datetime

class Datenbank:
    """
    Diese Klasse verwaltet die Datenbankverbindungen und -operationen für das Lager- und Bestellsystem.
    """
    
    def __init__(self):
        """
        Initialisiert die Datenbankverbindung und ruft die Methode zur Erstellung der Tabellen auf.
        Erstellt eine SQLite-Datenbank für die Lager- und Automatenbestände sowie Benutzerverwaltung.
        """
        start_time = time.time()
        self.db_conn = sqlite3.connect('lagerbestand.db', check_same_thread=False)
        self.cursor = self.db_conn.cursor()
        self._initialize_database()
        self.kanal_liste = {}  # Dynamische Kanäle mit Medikamentennamen
        print(f"Datenbankinitialisierung: {time.time() - start_time:.5f} Sekunden")
    
    def _initialize_database(self):
        """
        Erstellt die erforderlichen Tabellen, falls sie nicht existieren.
        Dazu gehören Tabellen für Lagerbestand, Automatenbestand, Warnungen und Bestellungen.
        """
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS lagerbestand (
                barcode TEXT PRIMARY KEY,
                name TEXT,
                menge INTEGER,
                verfallsdatum TEXT,
                ort TEXT DEFAULT 'Lager',
                kanal TEXT DEFAULT NULL
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS automatenbestand (
                barcode TEXT PRIMARY KEY,
                name TEXT,
                menge INTEGER,
                verfallsdatum TEXT,
                ort TEXT DEFAULT 'Automat',
                FOREIGN KEY (barcode) REFERENCES lagerbestand(barcode)
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS warnungen (
                barcode TEXT PRIMARY KEY,
                name TEXT,
                verfallsdatum TEXT,
                ort TEXT,
                status TEXT DEFAULT 'Offen'
            )
        ''')
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS bestellungen (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bestellgruppe_id INTEGER,
                kundennummer TEXT,
                barcode TEXT,
                name TEXT,
                bestelldatum TEXT,
                status TEXT DEFAULT 'Offen'
            )
        """)

        self.db_conn.commit()
        
        # Benutzer-Datenbank erstellen
        with sqlite3.connect('users.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kundennummer TEXT UNIQUE,
                    username TEXT UNIQUE,
                    password_hash TEXT,
                    role TEXT DEFAULT 'user'
                )
            ''')
            conn.commit()

    def log_aktion(self, aktion):
        """
        Protokolliert eine Aktion im Log-Protokoll.

        :param aktion: Beschreibung der durchgeführten Aktion
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        kundennummer = st.session_state.get("kundennummer", "Unbekannt")
        log_entry = [timestamp, kundennummer, aktion]

        with open("log_protokoll.csv", mode="a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(log_entry)
