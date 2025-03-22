import os
import pandas as pd
import sqlite3
import csv
from datenbank import Datenbank


class Admin:
    """
    Die Admin-Klasse verwaltet die Bestellungen, Benutzer und Logdateien in der Anwendung.
    """

    def __init__(self):
        """
        Initialisiert die Verbindung zur Datenbank und erstellt ein Datenbank-Objekt.
        """
        base_dir = os.path.dirname(__file__)
        self.db_path = os.path.join(base_dir, 'databases', 'lagerbestand.db')
        self.user_db_path = os.path.join(base_dir, 'databases', 'users.db')
        self.log_path = os.path.join(base_dir, 'logs', 'log_protokoll.csv')

        self.db_conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.db_conn.cursor()
        self.datenbank = Datenbank()

    def get_bestellungen(
        self,
        bestell_id_filter=None,
        kundennummer_filter=None,
        status=("Offen", "Genehmigt", "Storniert"),
    ):
        query = """
            SELECT bestellgruppe_id, kundennummer, GROUP_CONCAT(name, ', ') AS medikamente, bestelldatum, status
            FROM bestellungen
            WHERE status IN ({})
        """.format(",".join(["?"] * len(status)))

        params = list(status)

        if bestell_id_filter:
            query += " AND bestellgruppe_id LIKE ?"
            params.append(f"%{bestell_id_filter}%")

        if kundennummer_filter:
            query += " AND kundennummer LIKE ?"
            params.append(f"%{kundennummer_filter}%")

        query += " GROUP BY bestellgruppe_id, kundennummer ORDER BY bestelldatum DESC"

        self.cursor.execute(query, params)
        return pd.DataFrame(
            self.cursor.fetchall(),
            columns=["Bestell-ID", "Kundennummer", "Medikamente", "Bestelldatum", "Status"],
        )

    def get_logdatei(self, action_filter=None):
        """
        Liest die Logdatei aus und filtert nach Aktionen, falls gewünscht.
        """
        try:
            with open(self.log_path, encoding="utf-8") as file:
                reader = csv.reader(file)
                logs = list(reader)

                if not logs:
                    return pd.DataFrame(columns=["Zeitstempel", "Benutzer", "Aktion"])

                df = pd.DataFrame(logs, columns=["Zeitstempel", "Benutzer", "Aktion"])

                if action_filter and action_filter != "Alle":
                    df = df[df["Aktion"].str.contains(action_filter, na=False, case=False)]

                return df
        except FileNotFoundError:
            return pd.DataFrame(columns=["Zeitstempel", "Benutzer", "Aktion"])

    def get_users(self, username_filter=None):
        """
        Holt Benutzer aus der Datenbank und ermöglicht eine Filterung nach Benutzername.
        """
        with sqlite3.connect(self.user_db_path) as conn:
            cursor = conn.cursor()
            query = "SELECT id, kundennummer, username, role FROM users WHERE 1=1"
            params = []

            if username_filter:
                query += " AND username LIKE ?"
                params.append(f"%{username_filter}%")

            cursor.execute(query, params)
            return pd.DataFrame(
                cursor.fetchall(),
                columns=["ID", "Kundennummer", "Benutzername", "Rolle"],
            )

    def update_bestellstatus(self, bestell_id, status, bestellgruppe_id=None, medikamenten_namen=None):
        """
        Aktualisiert den Bestellstatus in der Datenbank und protokolliert die Aktion.
        """
        self.cursor.execute(
            "UPDATE bestellungen SET status = ? WHERE bestellgruppe_id = ?",
            (status, bestell_id),
        )
        self.db_conn.commit()

        if bestellgruppe_id and medikamenten_namen:
            self.datenbank.log_aktion(
                f"📦 Bestellung {bestellgruppe_id} aufgegeben mit Medikamenten: {', '.join(medikamenten_namen)}"
            )
        else:
            self.datenbank.log_aktion(
                f"📦 Bestellstatus für ID {bestell_id} wurde auf '{status}' gesetzt."
            )
