import streamlit as st
import pandas as pd
import sqlite3
import bcrypt
import time
import csv
import random
from datetime import datetime
from datenbank import Datenbank


class Automat:
    def __init__(self):
        self.db_conn = sqlite3.connect('lagerbestand.db', check_same_thread=False)
        self.cursor = self.db_conn.cursor()
        self.datenbank = Datenbank()
        self.kanal_liste = []

    def ware_zum_automaten_hinzufuegen(self, barcode):
        """Verschiebt eine Ware aus dem Lager in den Automaten, falls sie nicht abgelaufen ist."""
        try:
            # Überprüfen, ob der Barcode überhaupt eingegeben wurde
            if not barcode:
                print("\033[91m" + "🚫 Fehler: Barcode darf nicht leer sein!" + "\033[0m")
                return "🚫 Fehler: Barcode darf nicht leer sein!"

            # Ware aus der Datenbank abrufen
            self.cursor.execute("SELECT name, verfallsdatum FROM lagerbestand WHERE barcode = ?", (barcode,))
            row = self.cursor.fetchone()

            if row:
                name, verfallsdatum = row
                today = datetime.today().strftime('%Y-%m-%d')

                if verfallsdatum < today:
                    print("\033[91m" + f"🚫 Fehler: {name} (Barcode: {barcode}) ist abgelaufen und kann nicht in den Automaten verschoben werden!" + "\033[0m")
                    return f"🚫 Fehler: {name} (Barcode: {barcode}) ist abgelaufen und kann nicht in den Automaten verschoben werden!"

                # Prüfen, ob bereits ein Kanal für dieses Medikament existiert
                self.cursor.execute("SELECT DISTINCT kanal FROM lagerbestand WHERE name = ? AND ort = 'Automat'", (name,))
                existing_kanal = self.cursor.fetchone()

                if existing_kanal and existing_kanal[0]:  # Falls das Medikament bereits in einem Kanal ist
                    kanal = existing_kanal[0]
                else:
                    # Falls noch kein Kanal existiert, den nächsten verfügbaren zuweisen
                    self.cursor.execute("SELECT DISTINCT kanal FROM lagerbestand WHERE ort = 'Automat'")
                    vorhandene_kanaele = {row[0] for row in self.cursor.fetchall() if row[0]}
                    
                    neue_kanalnummer = 1
                    while f"Kanal {neue_kanalnummer}" in vorhandene_kanaele:
                        neue_kanalnummer += 1
                    
                    kanal = f"Kanal {neue_kanalnummer}"

                # Medikament in den Automaten verschieben
                self.cursor.execute("UPDATE lagerbestand SET ort = 'Automat', kanal = ? WHERE barcode = ?", (kanal, barcode))
                self.db_conn.commit()
                
                print("\033[92m" + f"✅ Erfolg: Ware {name} wurde in den Automaten verschoben (Kanal: {kanal})." + "\033[0m")
                message = f"✅ Erfolg: Ware {name} wurde in den Automaten verschoben (Kanal: {kanal})."

            else:
                print("\033[91m" + f"🚫 Fehler: Ware {barcode} nicht im Lagerbestand!" + "\033[0m")
                message = f"🚫 Fehler: Ware {barcode} nicht im Lagerbestand!"

        except sqlite3.OperationalError:
            # Fehler, wenn die Datenbank nicht verfügbar ist
            print("\033[91m" + "🚫 Fehler: Datenbank ist nicht verfügbar!" + "\033[0m")
            message = "🚫 Fehler: Datenbank ist nicht verfügbar!"

        except sqlite3.IntegrityError:
            # Fehler bei Datenbankintegrität
            print("\033[91m" + "🚫 Fehler: Integritätsproblem in der Datenbank!" + "\033[0m")
            message = "🚫 Fehler: Integritätsproblem in der Datenbank!"

        except Exception as e:
            # Allgemeiner Fehlerfall
            print("\033[91m" + f"🚫 Unbekannter Fehler: {str(e)}" + "\033[0m")
            message = f"🚫 Unbekannter Fehler: {str(e)}"
        
        # Aktion protokollieren und Nachricht zurückgeben
        self.datenbank.log_aktion(f"Automatenzugabe: {message}")
        return message



    def ware_aus_automaten_entfernen(self, barcode):
        """Entfernt eine Ware aus dem Automaten und legt sie zurück ins Lager."""
        try:
            # Überprüfen, ob der Barcode überhaupt eingegeben wurde
            if not barcode:
                print("\033[91m" + "🚫 Fehler: Barcode darf nicht leer sein!" + "\033[0m")
                return "🚫 Fehler: Barcode darf nicht leer sein!"

            # Überprüfen, ob die Ware im Automaten ist
            self.cursor.execute("SELECT kanal, name FROM lagerbestand WHERE barcode = ? AND ort = 'Automat'", (barcode,))
            row = self.cursor.fetchone()

            if row:
                kanal, name = row
                # Ware aus dem Automaten entfernen und ins Lager legen
                self.cursor.execute("UPDATE lagerbestand SET ort = 'Lager', kanal = NULL WHERE barcode = ?", (barcode,))
                self.db_conn.commit()
                
                # Prüfen, ob noch weitere Medikamente im selben Kanal vorhanden sind
                self.cursor.execute("SELECT COUNT(*) FROM lagerbestand WHERE kanal = ? AND ort = 'Automat'", (kanal,))
                count = self.cursor.fetchone()[0]
                if count == 0:
                    # Wenn der Kanal leer ist, aus der Kanal-Liste entfernen
                    if name in self.kanal_liste:
                        del self.kanal_liste[name]

                print("\033[92m" + f"✅ Erfolg: Ware {barcode} aus Kanal {kanal} entfernt und zurück ins Lager gelegt." + "\033[0m")
                message = f"✅ Erfolg: Ware {barcode} aus Kanal {kanal} entfernt und zurück ins Lager gelegt."
            
            else:
                # Fehler, wenn die Ware nicht im Automaten gefunden wurde
                print("\033[91m" + f"🚫 Fehler: Ware {barcode} nicht im Automaten!" + "\033[0m")
                message = f"🚫 Fehler: Ware {barcode} nicht im Automaten!"

        except sqlite3.OperationalError:
            # Fehler, wenn die Datenbank nicht verfügbar ist
            print("\033[91m" + "🚫 Fehler: Datenbank ist nicht verfügbar!" + "\033[0m")
            message = "🚫 Fehler: Datenbank ist nicht verfügbar!"

        except sqlite3.IntegrityError:
            # Fehler bei Datenbankintegrität
            print("\033[91m" + "🚫 Fehler: Integritätsproblem in der Datenbank!" + "\033[0m")
            message = "🚫 Fehler: Integritätsproblem in der Datenbank!"

        except KeyError:
            # Fehler, wenn der Name nicht in kanal_liste gefunden wird
            print("\033[91m" + "🚫 Fehler: Kanal konnte nicht aus der Liste entfernt werden!" + "\033[0m")
            message = "🚫 Fehler: Kanal konnte nicht aus der Liste entfernt werden!"

        except Exception as e:
            # Allgemeiner Fehlerfall
            print("\033[91m" + f"🚫 Unbekannter Fehler: {str(e)}" + "\033[0m")
            message = f"🚫 Unbekannter Fehler: {str(e)}"
        
        # Aktion protokollieren und Nachricht zurückgeben
        self.datenbank.log_aktion(f"Automatenentfernung: {message}")
        return message
    
    def ware_zum_warenkorb_hinzufuegen(self, barcode):
        """Fügt ein Medikament in den Warenkorb hinzu, wenn es im Automaten ist und nicht abgelaufen ist."""
        try:
            # Überprüfen, ob der Barcode überhaupt eingegeben wurde
            if not barcode:
                print("\033[91m" + "🚫 Fehler: Barcode darf nicht leer sein!" + "\033[0m")
                return "🚫 Fehler: Barcode darf nicht leer sein!"

            # Überprüfen, ob das Medikament bereits im Warenkorb ist
            if any(item["barcode"] == barcode for item in st.session_state.warenkorb):
                print("\033[91m" + f"🚫 Fehler: Barcode {barcode} ist bereits im Warenkorb!" + "\033[0m")
                return f"🚫 Fehler: Barcode {barcode} ist bereits im Warenkorb!"

            # Überprüfen, ob das Medikament im Automaten ist
            self.cursor.execute("SELECT name, verfallsdatum FROM lagerbestand WHERE barcode = ? AND ort = 'Automat'", (barcode,))
            row = self.cursor.fetchone()

            if not row:
                print("\033[91m" + f"🚫 Fehler: Medikament {barcode} ist nicht im Automaten!" + "\033[0m")
                self.datenbank.log_aktion(f"🚫 Fehler: Medikament {barcode} ist nicht im Automaten und kann nicht in den Warenkorb gelegt werden!")
                return f"🚫 Fehler: Medikament {barcode} ist nicht im Automaten!"

            name, verfallsdatum = row
            today = datetime.today().strftime('%Y-%m-%d')

            # Überprüfen, ob das Medikament abgelaufen ist
            if verfallsdatum < today:
                print("\033[93m" + f"⚠️ Fehler: {name} (Barcode: {barcode}) ist abgelaufen und kann nicht in den Warenkorb gelegt werden!" + "\033[0m")
                self.log_aktion(f"⚠️ Fehler: {name} (Barcode: {barcode}) ist abgelaufen und kann nicht in den Warenkorb gelegt werden!")
                return f"⚠️ Fehler: {name} (Barcode: {barcode}) ist abgelaufen!"

            # Medikament in den Warenkorb legen
            st.session_state.warenkorb.append({"barcode": barcode, "name": name, "verfallsdatum": verfallsdatum})
            
            print("\033[92m" + f"✅ {name} wurde dem Warenkorb hinzugefügt!" + "\033[0m")
            self.datenbank.log_aktion(f"✅ Medikament {name} (Barcode: {barcode}) zum Warenkorb hinzugefügt")

            return f"✅ {name} wurde dem Warenkorb hinzugefügt!"
        
        except sqlite3.OperationalError:
            # Fehler, wenn die Datenbank nicht verfügbar ist
            print("\033[91m" + "🚫 Fehler: Datenbank ist nicht verfügbar!" + "\033[0m")
            message = "🚫 Fehler: Datenbank ist nicht verfügbar!"

        except sqlite3.IntegrityError:
            # Fehler bei Datenbankintegrität
            print("\033[91m" + "🚫 Fehler: Integritätsproblem in der Datenbank!" + "\033[0m")
            message = "🚫 Fehler: Integritätsproblem in der Datenbank!"

        except KeyError:
            # Fehler, wenn warenkorb nicht in session_state gefunden wird
            print("\033[91m" + "🚫 Fehler: Warenkorb konnte nicht gefunden werden!" + "\033[0m")
            message = "🚫 Fehler: Warenkorb konnte nicht gefunden werden!"

        except Exception as e:
            # Allgemeiner Fehlerfall
            print("\033[91m" + f"🚫 Unbekannter Fehler: {str(e)}" + "\033[0m")
            message = f"🚫 Unbekannter Fehler: {str(e)}"
        
        # Aktion protokollieren und Nachricht zurückgeben
        self.datenbank.log_aktion(f"Warenkorb-Hinzufügen: {message}")
        return message


    def bestellung_abschicken(self, kundennummer):
        """Speichert eine Warenkorb-Bestellung mit einer gemeinsamen Bestellgruppen-ID und entfernt Medikamente aus dem Automaten."""
        try:
            # Überprüfen, ob die Kundennummer eingegeben wurde
            if not kundennummer:
                print("\033[91m" + "🚫 Fehler: Kundennummer darf nicht leer sein!" + "\033[0m")
                return "🚫 Fehler: Kundennummer darf nicht leer sein!"

            # Überprüfen, ob der Warenkorb leer ist
            if not st.session_state.warenkorb:
                print("\033[91m" + "🚫 Fehler: Warenkorb ist leer!" + "\033[0m")
                return "🚫 Fehler: Warenkorb ist leer!"

            bestelldatum = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
            bestellgruppe_id = random.randint(100000, 999999)
            medikamenten_namen = []

            for item in st.session_state.warenkorb:
                barcode, name = item["barcode"], item["name"]
                medikamenten_namen.append(name)

                # Überprüfen, ob das Medikament noch im Automaten ist
                self.cursor.execute("SELECT ort FROM lagerbestand WHERE barcode = ?", (barcode,))
                ort = self.cursor.fetchone()
                if not ort or ort[0] != 'Automat':
                    print("\033[91m" + f"🚫 Fehler: {name} (Barcode: {barcode}) ist nicht im Automaten und kann nicht bestellt werden!" + "\033[0m")
                    return f"🚫 Fehler: {name} (Barcode: {barcode}) ist nicht im Automaten und kann nicht bestellt werden!"

                # Bestellung in die Datenbank eintragen
                self.cursor.execute(
                    "INSERT INTO bestellungen (bestellgruppe_id, kundennummer, barcode, name, bestelldatum) VALUES (?, ?, ?, ?, ?)",
                    (bestellgruppe_id, kundennummer, barcode, name, bestelldatum)
                )

                # Medikament aus dem Automaten entfernen
                self.cursor.execute("DELETE FROM lagerbestand WHERE barcode = ?", (barcode,))

            self.db_conn.commit()
            st.session_state.warenkorb = []

            # Erfolgreiche Bestellung visuell anzeigen
            print("\033[92m" + f"✅ Bestellung {bestellgruppe_id} erfolgreich aufgegeben mit Medikamenten: {', '.join(medikamenten_namen)}" + "\033[0m")
            self.datenbank.log_aktion(f"📦 Bestellung {bestellgruppe_id} aufgegeben mit Medikamenten: {', '.join(medikamenten_namen)}")

            return f"✅ Bestellung {bestellgruppe_id} erfolgreich aufgegeben mit Medikamenten: {', '.join(medikamenten_namen)}"

        except sqlite3.OperationalError:
            # Fehler, wenn die Datenbank nicht verfügbar ist
            print("\033[91m" + "🚫 Fehler: Datenbank ist nicht verfügbar!" + "\033[0m")
            message = "🚫 Fehler: Datenbank ist nicht verfügbar!"

        except sqlite3.IntegrityError:
            # Fehler bei Datenbankintegrität
            print("\033[91m" + "🚫 Fehler: Integritätsproblem in der Datenbank!" + "\033[0m")
            message = "🚫 Fehler: Integritätsproblem in der Datenbank!"

        except KeyError:
            # Fehler, wenn warenkorb nicht in session_state gefunden wird
            print("\033[91m" + "🚫 Fehler: Warenkorb konnte nicht gefunden werden!" + "\033[0m")
            message = "🚫 Fehler: Warenkorb konnte nicht gefunden werden!"

        except Exception as e:
            # Allgemeiner Fehlerfall
            print("\033[91m" + f"🚫 Unbekannter Fehler: {str(e)}" + "\033[0m")
            message = f"🚫 Unbekannter Fehler: {str(e)}"
        
        # Aktion protokollieren und Nachricht zurückgeben
        self.datenbank.log_aktion(f"Bestellung: {message}")
        return message


    def get_bestellungen_gruppiert(self, kundennummer, status='Offen'):
        """Ruft alle Bestellungen eines Kunden ab und gruppiert sie nach Bestellgruppen-ID."""
        self.cursor.execute("""
            SELECT bestellgruppe_id, GROUP_CONCAT(name, ', ') AS medikamente, bestelldatum, status
            FROM bestellungen
            WHERE kundennummer = ? AND status = ?
            GROUP BY bestellgruppe_id
            ORDER BY bestelldatum DESC
        """, (kundennummer, status))
        
        data = self.cursor.fetchall()
        return pd.DataFrame(data, columns=["Bestell-ID", "Medikamente", "Bestelldatum", "Status"])
    
    def get_kanal_liste(self):
        """Gibt eine Liste aller gespeicherten Kanäle zurück."""
        return list(self.kanal_liste.keys())

    def get_belegte_kanaele(self):
        """Holt die Liste der belegten Kanäle im Automaten."""
        self.cursor.execute("SELECT DISTINCT kanal FROM lagerbestand WHERE ort = 'Automat' AND kanal IS NOT NULL")
        return [row[0] for row in self.cursor.fetchall()]
    

    def bestellung_stornieren(self, bestellgruppe_id, kundennummer):
        """Storniert eine gesamte Bestellung mit einer Bestellgruppen-ID und setzt den Status auf 'Storniert'."""
        try:
            # Überprüfen, ob die Bestellgruppen-ID und die Kundennummer eingegeben wurden
            if not bestellgruppe_id or not kundennummer:
                print("\033[91m" + "🚫 Fehler: Bestellgruppen-ID und Kundennummer dürfen nicht leer sein!" + "\033[0m")
                return "🚫 Fehler: Bestellgruppen-ID und Kundennummer dürfen nicht leer sein!"

            # Bestellungen abrufen, die storniert werden sollen
            self.cursor.execute(
                "SELECT barcode, name FROM bestellungen WHERE bestellgruppe_id = ? AND kundennummer = ? AND status = 'Offen'",
                (bestellgruppe_id, kundennummer)
            )
            bestellungen = self.cursor.fetchall()

            # Überprüfen, ob die Bestellung existiert und noch offen ist
            if not bestellungen:
                print("\033[91m" + "🚫 Fehler: Bestellung nicht gefunden oder bereits bearbeitet!" + "\033[0m")
                return "🚫 Fehler: Bestellung nicht gefunden oder bereits bearbeitet!"

            medikamente_zurueck = []

            # Medikamente zurück ins Lager einfügen
            for barcode, name in bestellungen:
                try:
                    # Überprüfen, ob das Medikament bereits im Lager ist
                    self.cursor.execute("SELECT menge FROM lagerbestand WHERE barcode = ? AND ort = 'Lager'", (barcode,))
                    vorhandenes_lager = self.cursor.fetchone()

                    if vorhandenes_lager:
                        # Wenn bereits vorhanden, Menge erhöhen
                        neue_menge = vorhandenes_lager[0] + 1
                        self.cursor.execute(
                            "UPDATE lagerbestand SET menge = ? WHERE barcode = ? AND ort = 'Lager'",
                            (neue_menge, barcode)
                        )
                    else:
                        # Ansonsten als neue Ware ins Lager einfügen
                        self.cursor.execute(
                            "INSERT INTO lagerbestand (barcode, name, menge, verfallsdatum, ort) VALUES (?, ?, 1, DATE('now', '+1 year'), 'Lager')",
                            (barcode, name)
                        )
                    medikamente_zurueck.append(name)

                except sqlite3.IntegrityError:
                    print("\033[91m" + f"🚫 Fehler: Integritätsproblem beim Zurücklegen von {name} (Barcode: {barcode})!" + "\033[0m")
                    return f"🚫 Fehler: Integritätsproblem beim Zurücklegen von {name} (Barcode: {barcode})!"

            # Bestellungen auf "Storniert" setzen anstatt zu löschen
            self.cursor.execute(
                "UPDATE bestellungen SET status = 'Storniert' WHERE bestellgruppe_id = ? AND kundennummer = ?",
                (bestellgruppe_id, kundennummer)
            )

            self.db_conn.commit()

            print("\033[92m" + f"✅ Bestellung {bestellgruppe_id} storniert! Alle Medikamente wurden zurück ins Lager gelegt." + "\033[0m")
            self.datenbank.log_aktion(f"📦 Bestellung {bestellgruppe_id} storniert, Medikamente zurück ins Lager: {', '.join(medikamente_zurueck)}")

            return f"✅ Bestellung {bestellgruppe_id} storniert! Alle Medikamente wurden zurück ins Lager gelegt und als 'Storniert' markiert."

        except sqlite3.OperationalError:
            # Fehler, wenn die Datenbank nicht verfügbar ist
            print("\033[91m" + "🚫 Fehler: Datenbank ist nicht verfügbar!" + "\033[0m")
            message = "🚫 Fehler: Datenbank ist nicht verfügbar!"

        except sqlite3.IntegrityError:
            # Fehler bei Datenbankintegrität
            print("\033[91m" + "🚫 Fehler: Integritätsproblem in der Datenbank!" + "\033[0m")
            message = "🚫 Fehler: Integritätsproblem in der Datenbank!"

        except Exception as e:
            # Allgemeiner Fehlerfall
            print("\033[91m" + f"🚫 Unbekannter Fehler: {str(e)}" + "\033[0m")
            message = f"🚫 Unbekannter Fehler: {str(e)}"

        # Aktion protokollieren und Nachricht zurückgeben
        self.datenbank.log_aktion(f"Bestellung Stornierung: {message}")
        return message