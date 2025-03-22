import pandas as pd
import sqlite3
from datetime import datetime
import os


class Warnung:
    """
    Eine Klasse zur Verwaltung von Warnungen für abgelaufene Medikamente und niedrige Bestände.
    """

    def __init__(self):
        """
        Initialisiert die Datenbankverbindung und den Cursor.
        """
        base_dir = os.path.dirname(__file__)  # src/lagersystem
        db_path = os.path.join(base_dir, 'databases', 'lagerbestand.db')

        # Verbindung herstellen
        self.db_conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.db_conn.cursor()

    def get_warnungen(self, ort_filter=None):
        """
        Ruft Warnungen aus der Datenbank ab und filtert optional nach Ort.

        :param ort_filter: Optionaler Filter für den Ort ("Lager" oder "Automat").
        :return: Ein DataFrame mit den Warnungen.
        """
        self._pruefe_warnungen()

        query = (
            "SELECT barcode, name, verfallsdatum, ort, status FROM warnungen WHERE 1=1"
        )
        params = []

        if ort_filter in ["Lager", "Automat"]:
            query += " AND ort = ?"
            params.append(ort_filter)

        self.cursor.execute(query, params)
        data = self.cursor.fetchall()

        return pd.DataFrame(
            data, columns=["Barcode", "Name", "Verfallsdatum", "Ort", "Status"]
        )

    def _pruefe_warnungen(self):
        """
        Überprüft die Datenbank auf abgelaufene Medikamente und niedrige Bestände, aktualisiert oder fügt neue Warnungen hinzu.
        """
        today = datetime.today().strftime("%Y-%m-%d")

        # Lösche veraltete Warnungen (z. B. wenn ein Medikament entfernt wurde)
        self.cursor.execute(
            "DELETE FROM warnungen WHERE barcode NOT IN (SELECT barcode FROM lagerbestand)"
        )

        # Finde alle abgelaufenen Medikamente im Lagerbestand
        self.cursor.execute(
            "SELECT barcode, name, verfallsdatum, ort FROM lagerbestand WHERE verfallsdatum < ?",
            (today,),
        )
        abgelaufene_medikamente = self.cursor.fetchall()

        for barcode, name, verfallsdatum, ort in abgelaufene_medikamente:
            self._update_or_insert_warnung(
                barcode, name, verfallsdatum, ort, "Medikament abgelaufen"
            )

        self.db_conn.commit()

    def _update_or_insert_warnung(self, barcode, name, verfallsdatum, ort, status):
        """
        Aktualisiert eine bestehende Warnung oder fügt eine neue hinzu.

        :param barcode: Der Barcode des Medikaments.
        :param name: Der Name des Medikaments.
        :param verfallsdatum: Das Verfallsdatum des Medikaments.
        :param ort: Der Lagerort des Medikaments.
        :param status: Der Status der Warnung (abgelaufen oder unter Schwellenwert).
        """
        self.cursor.execute(
            "SELECT ort, status FROM warnungen WHERE barcode = ?", (barcode,)
        )
        warnung = self.cursor.fetchone()

        if warnung:
            # Falls das Medikament bereits eine Warnung hat, aktualisiere den Ort oder Status
            if warnung[0] != ort or warnung[1] != status:
                self.cursor.execute(
                    "UPDATE warnungen SET ort = ?, status = ? WHERE barcode = ?",
                    (ort, status, barcode),
                )
        else:
            # Falls es noch keine Warnung gibt, wird eine neue erstellt
            self.cursor.execute(
                "INSERT INTO warnungen (barcode, name, verfallsdatum, ort, status) VALUES (?, ?, ?, ?, ?)",
                (barcode, name, verfallsdatum, ort, status),
            )
