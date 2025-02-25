import streamlit as st
import pandas as pd
import sqlite3
import bcrypt
import time
import csv
import random
from datetime import datetime


class Warnung:
    """
    Eine Klasse zur Verwaltung von Warnungen für abgelaufene Medikamente.
    """
    
    def __init__(self):
        """
        Initialisiert die Datenbankverbindung und den Cursor.
        """
        self.db_conn = sqlite3.connect('lagerbestand.db', check_same_thread=False)
        self.cursor = self.db_conn.cursor()
        
    def get_warnungen(self, ort_filter=None):
        """
        Ruft Warnungen aus der Datenbank ab und filtert optional nach Ort.
        
        :param ort_filter: Optionaler Filter für den Ort ("Lager" oder "Automat").
        :return: Ein DataFrame mit den Warnungen.
        """
        self._pruefe_warnungen()
        
        query = "SELECT barcode, name, verfallsdatum, ort, status FROM warnungen WHERE 1=1"
        params = []

        if ort_filter in ["Lager", "Automat"]:
            query += " AND ort = ?"
            params.append(ort_filter)

        self.cursor.execute(query, params)
        data = self.cursor.fetchall()

        return pd.DataFrame(data, columns=["Barcode", "Name", "Verfallsdatum", "Ort", "Status"])

    def _pruefe_warnungen(self):
        """
        Überprüft die Datenbank auf abgelaufene Medikamente und aktualisiert oder fügt neue Warnungen hinzu.
        """
        today = datetime.today().strftime('%Y-%m-%d')

        # Lösche veraltete Warnungen (z. B. wenn ein Medikament entfernt wurde)
        self.cursor.execute("DELETE FROM warnungen WHERE barcode NOT IN (SELECT barcode FROM lagerbestand)")
        
        # Finde alle abgelaufenen Medikamente im Lagerbestand
        self.cursor.execute("SELECT barcode, name, verfallsdatum, ort FROM lagerbestand WHERE verfallsdatum < ?", (today,))
        abgelaufene_medikamente = self.cursor.fetchall()

        for barcode, name, verfallsdatum, ort in abgelaufene_medikamente:
            self.cursor.execute("SELECT ort FROM warnungen WHERE barcode = ?", (barcode,))
            warnung = self.cursor.fetchone()

            if warnung:
                # Falls das Medikament bereits eine Warnung hat, aber der Ort anders ist, wird der Ort aktualisiert
                if warnung[0] != ort:
                    self.cursor.execute("UPDATE warnungen SET ort = ? WHERE barcode = ?", (ort, barcode))
            else:
                # Falls es noch keine Warnung gibt, wird eine neue erstellt
                self.cursor.execute("INSERT INTO warnungen (barcode, name, verfallsdatum, ort) VALUES (?, ?, ?, ?)", 
                                    (barcode, name, verfallsdatum, ort))
        
        self.db_conn.commit()
