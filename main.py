import streamlit as st
import pandas as pd
import sqlite3
import bcrypt
import time
import csv
import random
from datetime import datetime

# 🔴 Muss die erste Streamlit-Funktion sein!
st.set_page_config(page_title="Lagersystem für Medikamente", layout="centered")

class Lagersystem:
    def __init__(self):
        start_time = time.time()
        self.db_conn = sqlite3.connect('lagerbestand.db', check_same_thread=False)
        self.cursor = self.db_conn.cursor()
        self._initialize_database()
        self.kanal_liste = {}  # Dynamische Kanäle mit Medikamentennamen
        print(f"Datenbankinitialisierung: {time.time() - start_time:.5f} Sekunden")
    
    def _initialize_database(self):
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
        with sqlite3.connect('users.db') as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kundennummer TEXT UNIQUE,
                    username TEXT UNIQUE,
                    password_hash TEXT
                )
            ''')
            conn.commit()

    def get_kanal_liste(self):
        return list(self.kanal_liste.keys())


    def log_aktion(self, aktion):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        kundennummer = st.session_state.get("kundennummer", "Unbekannt")
        log_entry = [timestamp, kundennummer, aktion]

        with open("log_protokoll.csv", mode="a", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(log_entry)

    
    def ware_hinzufuegen(self, barcode, name, verfallsdatum, ort='Lager'):
        self.cursor.execute("SELECT * FROM lagerbestand WHERE barcode = ?", (barcode,))
        row = self.cursor.fetchone()

        if row:
            message = f"Fehler: Barcode {barcode} existiert bereits!"
        else:
            self.cursor.execute("INSERT INTO lagerbestand (barcode, name, menge, verfallsdatum, ort) VALUES (?, ?, 1, ?, ?)", 
                                (barcode, name, verfallsdatum, ort))
            self.db_conn.commit()
            message = f"Erfolg: {name} hinzugefügt."

        self.log_aktion(f"Ware hinzufügen: {message}")
        return message

    def ware_entfernen(self, barcode):
        """Entfernt eine Ware nur, wenn sie im Lager ist. Medikamente im Automaten können nicht gelöscht werden."""
        
        # Überprüfen, ob das Medikament im Lager ist
        self.cursor.execute("SELECT ort FROM lagerbestand WHERE barcode = ?", (barcode,))
        row = self.cursor.fetchone()

        if row:
            ort = row[0]
            if ort == "Lager":
                self.cursor.execute("DELETE FROM lagerbestand WHERE barcode = ?", (barcode,))
                self.db_conn.commit()
                message = f"✅ Erfolg: Ware {barcode} aus dem Lager entfernt."
            else:
                message = f"❌ Fehler: Ware {barcode} ist im Automaten und kann nicht gelöscht werden!"
        else:
            message = f"❌ Fehler: Barcode {barcode} nicht im Lagersystem gefunden!"

        self.log_aktion(f"Ware entfernen: {message}")
        return message


    def get_lagerbestand(self, barcode_filter=None, ort_filter=None):
        self._pruefe_warnungen()
        
        query = "SELECT barcode, name, menge, verfallsdatum, ort, kanal FROM lagerbestand WHERE 1=1"
        params = []

        if ort_filter in ["Lager", "Automat"]:
            query += " AND ort = ?"
            params.append(ort_filter)

        if barcode_filter:
            query += " AND barcode LIKE ?"
            params.append(f"%{barcode_filter}%")

        self.cursor.execute(query, params)
        data = self.cursor.fetchall()

        df = pd.DataFrame(data, columns=["Barcode", "Name", "Menge", "Verfallsdatum", "Ort", "Kanal"])
        return df



    def get_artikel_anzahl(self):
        self.cursor.execute("SELECT name, SUM(menge) as total FROM lagerbestand GROUP BY name")
        data = self.cursor.fetchall()
        return pd.DataFrame(data, columns=["Name", "Menge"])  # Jetzt hat die Abfrage nur zwei Spalten
    
    def get_artikel_namen(self):
        self.cursor.execute("SELECT DISTINCT name FROM lagerbestand")
        data = self.cursor.fetchall()
        return [row[0] for row in data]  # Extrahiert nur die Namen in eine Liste
    
    def get_warnungen(self, ort_filter=None):
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


    def ware_zum_automaten_hinzufuegen(self, barcode):
        self.cursor.execute("SELECT name, verfallsdatum FROM lagerbestand WHERE barcode = ?", (barcode,))
        row = self.cursor.fetchone()

        if row:
            name, verfallsdatum = row
            today = datetime.today().strftime('%Y-%m-%d')

            if verfallsdatum < today:
                message = f"Fehler: {name} (Barcode: {barcode}) ist abgelaufen und kann nicht in den Automaten verschoben werden!"
            else:
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
                message = f"Erfolg: Ware {name} wurde in den Automaten verschoben (Kanal: {kanal})."

        else:
            message = f"Fehler: Ware {barcode} nicht im Lagerbestand!"

        self.log_aktion(f"Automatenzugabe: {message}")
        return message


    def ware_aus_automaten_entfernen(self, barcode):
        self.cursor.execute("SELECT kanal, name FROM lagerbestand WHERE barcode = ? AND ort = 'Automat'", (barcode,))
        row = self.cursor.fetchone()

        if row:
            kanal, name = row
            self.cursor.execute("UPDATE lagerbestand SET ort = 'Lager', kanal = NULL WHERE barcode = ?", (barcode,))
            self.db_conn.commit()
            
            # Prüfen, ob noch weitere Medikamente im Kanal vorhanden sind
            self.cursor.execute("SELECT COUNT(*) FROM lagerbestand WHERE kanal = ? AND ort = 'Automat'", (kanal,))
            count = self.cursor.fetchone()[0]
            if count == 0:
                del self.kanal_liste[name]
            
            message = f"Erfolg: Ware {barcode} aus Kanal {kanal} entfernt und zurück ins Lager gelegt."
        else:
            message = f"Fehler: Ware {barcode} nicht im Automaten!"

        self.log_aktion(f"Automatenentfernung: {message}")
        return message



        
    def hash_password(self, password):
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def verify_password(self, password, hashed):
        return bcrypt.checkpw(password.encode(), hashed.encode())

    def generate_kundennummer(self):
        return str(random.randint(10000000, 99999999))

    def register_user(self, username, password):
        kundennummer = str(random.randint(10000000, 99999999))
        hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        try:
            with sqlite3.connect('users.db') as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users (kundennummer, username, password_hash) VALUES (?, ?, ?)", 
                               (kundennummer, username, hashed_pw))
                conn.commit()
            return kundennummer
        except sqlite3.IntegrityError:
            return None

    def get_user(self, username):
        with sqlite3.connect('users.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT kundennummer, password_hash FROM users WHERE username = ?", (username,))
            return cursor.fetchone()
        
    def get_offene_bestellungen(self, kundennummer):
        """Gibt eine Liste von offenen Bestellungen für das Dropdown-Menü zurück."""
        self.cursor.execute("SELECT id, name FROM bestellungen WHERE kundennummer = ? AND status = 'Offen'", (kundennummer,))
        return self.cursor.fetchall()  # Gibt eine Liste von (id, name)-Tupeln zurück


    def ware_zum_warenkorb_hinzufuegen(self, barcode):
        """Fügt ein Medikament in den Warenkorb hinzu, wenn es im Automaten ist und nicht abgelaufen ist."""
        
        if any(item["barcode"] == barcode for item in st.session_state.warenkorb):
            return f"❌ Fehler: Barcode {barcode} ist bereits im Warenkorb!"

        self.cursor.execute("SELECT name, verfallsdatum FROM lagerbestand WHERE barcode = ? AND ort = 'Automat'", (barcode,))
        row = self.cursor.fetchone()

        if not row:
            self.log_aktion(f"❌ Fehler: Medikament {barcode} ist nicht im Automaten und kann nicht in den Warenkorb gelegt werden!")
            return f"❌ Fehler: Medikament {barcode} ist nicht im Automaten!"

        name, verfallsdatum = row
        today = datetime.today().strftime('%Y-%m-%d')

        if verfallsdatum < today:
            self.log_aktion(f"⚠️ Fehler: {name} (Barcode: {barcode}) ist abgelaufen und kann nicht in den Warenkorb gelegt werden!")
            return f"⚠️ Fehler: {name} (Barcode: {barcode}) ist abgelaufen!"

        st.session_state.warenkorb.append({"barcode": barcode, "name": name, "verfallsdatum": verfallsdatum})
        
        # Loggen der Aktion
        self.log_aktion(f"✅ Medikament {name} (Barcode: {barcode}) zum Warenkorb hinzugefügt")

        return f"✅ {name} wurde dem Warenkorb hinzugefügt!"




    def bestellung_abschicken(self, kundennummer):
        """Speichert eine Warenkorb-Bestellung mit einer gemeinsamen Bestellgruppen-ID und entfernt Medikamente aus dem Automaten."""
        
        if not st.session_state.warenkorb:
            return "❌ Fehler: Warenkorb ist leer!"

        bestelldatum = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
        bestellgruppe_id = random.randint(100000, 999999)
        medikamenten_namen = []

        for item in st.session_state.warenkorb:
            barcode, name = item["barcode"], item["name"]
            medikamenten_namen.append(name)

            self.cursor.execute(
                "INSERT INTO bestellungen (bestellgruppe_id, kundennummer, barcode, name, bestelldatum) VALUES (?, ?, ?, ?, ?)",
                (bestellgruppe_id, kundennummer, barcode, name, bestelldatum)
            )

            self.cursor.execute("DELETE FROM lagerbestand WHERE barcode = ?", (barcode,))

        self.db_conn.commit()
        st.session_state.warenkorb = []

        # Loggen der Bestellung mit Medikamentennamen
        self.log_aktion(f"📦 Bestellung {bestellgruppe_id} aufgegeben mit Medikamenten: {', '.join(medikamenten_namen)}")

        return f"✅ Bestellung {bestellgruppe_id} erfolgreich aufgegeben mit Medikamenten: {', '.join(medikamenten_namen)}"




    def ware_aus_automaten_entfernen(self, barcode):
        self.cursor.execute("SELECT kanal, name FROM lagerbestand WHERE barcode = ? AND ort = 'Automat'", (barcode,))
        row = self.cursor.fetchone()

        if row:
            kanal, name = row
            self.cursor.execute("UPDATE lagerbestand SET ort = 'Lager', kanal = NULL WHERE barcode = ?", (barcode,))
            self.db_conn.commit()

            # Prüfen, ob noch weitere Medikamente im Kanal vorhanden sind
            self.cursor.execute("SELECT COUNT(*) FROM lagerbestand WHERE kanal = ? AND ort = 'Automat'", (kanal,))
            count = self.cursor.fetchone()[0]

            # Nur löschen, wenn keine weiteren Medikamente mit diesem Namen in diesem Kanal sind
            if count == 0 and name in self.kanal_liste:
                del self.kanal_liste[name]

            message = f"Erfolg: Ware {barcode} aus Kanal {kanal} entfernt und zurück ins Lager gelegt."
        else:
            message = f"Fehler: Ware {barcode} nicht im Automaten!"

        self.log_aktion(f"Automatenentfernung: {message}")
        return message



    
    def get_bestellungen_gruppiert(self, kundennummer):
        """Ruft alle Bestellungen eines Kunden ab und gruppiert sie nach Bestellgruppen-ID."""
        self.cursor.execute("""
            SELECT bestellgruppe_id, GROUP_CONCAT(name, ', ') AS medikamente, bestelldatum, status
            FROM bestellungen
            WHERE kundennummer = ?
            GROUP BY bestellgruppe_id
            ORDER BY bestelldatum DESC
        """, (kundennummer,))
        
        data = self.cursor.fetchall()
        return pd.DataFrame(data, columns=["Bestell-ID", "Medikamente", "Bestelldatum", "Status"])
    
    def get_belegte_kanaele(self):
        self.cursor.execute("SELECT DISTINCT kanal FROM lagerbestand WHERE ort = 'Automat' AND kanal IS NOT NULL")
        return [row[0] for row in self.cursor.fetchall()]
    
    def bestellung_stornieren(self, bestellgruppe_id, kundennummer):
        """Storniert eine gesamte Bestellung mit einer Bestellgruppen-ID und fügt die Medikamente zurück ins Lager ein."""
        
        # Bestellungen abrufen, die storniert werden sollen
        self.cursor.execute(
            "SELECT barcode, name FROM bestellungen WHERE bestellgruppe_id = ? AND kundennummer = ? AND status = 'Offen'",
            (bestellgruppe_id, kundennummer)
        )
        bestellungen = self.cursor.fetchall()

        if not bestellungen:
            return "❌ Fehler: Bestellung nicht gefunden oder bereits bearbeitet!"

        medikamente_zurueck = []
        
        # Medikamente zurück ins Lager einfügen
        for barcode, name in bestellungen:
            self.cursor.execute(
                "INSERT INTO lagerbestand (barcode, name, menge, verfallsdatum, ort) VALUES (?, ?, 1, DATE('now', '+1 year'), 'Lager')",
                (barcode, name)
            )
            medikamente_zurueck.append(name)

        # Bestellung aus der Datenbank löschen
        self.cursor.execute("DELETE FROM bestellungen WHERE bestellgruppe_id = ?", (bestellgruppe_id,))
        self.db_conn.commit()

        # Log-Eintrag für die Stornierung
        self.log_aktion(f"Bestellung {bestellgruppe_id} storniert, Medikamente zurück ins Lager: {', '.join(medikamente_zurueck)}")

        return f"✅ Bestellung {bestellgruppe_id} storniert! Alle Medikamente wurden zurück ins Lager gelegt."


        




        
# **Streamlit App Start**
lagersystem = Lagersystem()

# **Streamlit Custom Styles für ein seriöses Design**
st.markdown("""
    <style>
        /* Gesamter Hintergrund */
        .stApp {
            background: linear-gradient(180deg, #ffffff 10%, #f0f4f8 100%);
            font-family: 'Arial', sans-serif;
        }
        
        /* Titel in der Box */
        .login-title {
            font-size: 32px; 
            font-weight: bold;
            color: #003366;
            margin-bottom: 50px;
            text-align: center;
        }

        /* Eingabefelder */
        .login-input {
            width: 100%;
            padding: 12px;
            margin: 8px 0;
            border: 1px solid #004080;
            border-radius: 6px;
            box-sizing: border-box;
            font-size: 14px;
            background-color: #f8f9fa;
        }

        /* Button */
        .login-button {
            width: 100%;
            background-color: #003366;
            color: white;
            font-size: 16px;
            border-radius: 8px;
            padding: 12px;
            border: none;
            transition: background-color 0.3s ease;
            font-weight: bold;
        }

        .login-button:hover {
            background-color: #00224d;
        }

        /* Tab-Menü */
        .stTabs [role="tablist"] {
            display: flex;
            justify-content: center;
            border-bottom: 2px solid #004080;
        }

        .stTabs [role="tab"] {
            font-weight: bold;
            color: #003366;
        }

        .stTabs [role="tab"][aria-selected="true"] {
            border-bottom: 3px solid #003366 !important;
        }

        /* Erfolgs- & Fehlermeldungen */
        .message {
            font-size: 14px;
            margin-top: 10px;
            color: #0066cc;
        }
    </style>
    """, unsafe_allow_html=True)

# **Session State für Authentifizierung**
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.kundennummer = None
    st.session_state.username = None

# **Login- oder Registrierungsanzeige**
if not st.session_state.authenticated:
    
    # Die Überschrift ist jetzt innerhalb der Box!
    st.markdown('<p class="login-title">Lagersystem Anmeldung</p>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🔑 Login", "🆕 Registrierung"])

    # **Login-Bereich**
    with tab1:
        username = st.text_input("Benutzername", key="login_username")
        password = st.text_input("Passwort", type="password", key="login_password")

        if st.button("Anmelden", key="login_button", help="Melden Sie sich mit Ihrem Account an", use_container_width=True):
            user_data = lagersystem.get_user(username)
            if user_data and lagersystem.verify_password(password, user_data[1]):
                st.session_state.authenticated = True
                st.session_state.kundennummer = user_data[0]
                st.session_state.username = username
                lagersystem.log_aktion("Login erfolgreich")
                st.rerun()
            else:
                lagersystem.log_aktion("Login fehlgeschlagen")
                st.error("❌ Falscher Benutzername oder Passwort!")

    # **Registrierungs-Bereich**
    with tab2:
        new_username = st.text_input("Neuer Benutzername", key="register_username")
        new_password = st.text_input("Neues Passwort", type="password", key="register_password")

        if st.button("Registrieren", key="register_button", help="Neuen Benutzer anlegen", use_container_width=True):
            if new_username and new_password:
                kundennummer = lagersystem.register_user(new_username, new_password)
                if kundennummer:
                    st.success(f"✅ Erfolgreich registriert! Ihre Kundennummer: {kundennummer}")
                    st.session_state.authenticated = True
                    st.session_state.kundennummer = kundennummer
                    st.session_state.username = username
                    lagersystem.log_aktion("Registrierung erfolgreich")
                    st.rerun()
                else:
                    lagersystem.log_aktion("Benutzername vergeben")
                    st.error("⚠️ Benutzername bereits vergeben!")
            else:
                lagersystem.log_aktion("Registrierung fehlgeschlagen")
                st.error("⚠️ Bitte alle Felder ausfüllen!")

    st.markdown("</div>", unsafe_allow_html=True)


# **Sidebar: Kundennummer & Logout**
if st.session_state.authenticated:
    if "warenkorb" not in st.session_state:
        st.session_state.warenkorb = []

    with st.sidebar:
        # Menü erstellen
        menu = ["Startseite", "Lagersystem", "Automat", "Warnungen verwalten"]
        choice = st.radio("Wählen Sie das System", menu)

        # Trennlinie
        st.markdown("---")



        st.markdown("<br><br><br><br><br><br><br><br><br>", unsafe_allow_html=True) 
        st.markdown(f"**Kundennummer:** `{st.session_state.get('kundennummer', 'Nicht gesetzt')}`")

        

        # Logout-Button
        if st.button("🚪 Abmelden", help="Klicken Sie hier, um sich abzumelden", use_container_width=True, key="logout_button"):
            st.session_state.authenticated = False
            lagersystem.log_aktion("Logout erfolgreich")
            st.session_state.kundennummer = None
            st.session_state.username = None
            st.rerun()
    #st.title("Lagersystem für Medikamente")
    
    if choice == "Startseite":
        st.subheader("📦 Medikamentenübersicht")

        tab1, tab2 = st.tabs(["📋 Gesamtübersicht", "🔍 Artikelübersicht"])

        with tab1:
            st.subheader("📋 Gesamtübersicht der Medikamente")

            warnungen = lagersystem.get_warnungen()
            if not warnungen.empty:
                st.warning("⚠️ Es gibt abgelaufene Medikamente! Überprüfen Sie den Reiter 'Warnungen verwalten'.")

            # Layout für Suche & Filter
            col1, col2 = st.columns([2, 2])  
            with col1:
                barcode_search_startseite = st.text_input("🔍 Barcode suchen")
            with col2:
                ort_filter_startseite = st.selectbox("📍 Ort filtern", ["Alle", "Lager", "Automat"], index=0)

            # Medikamentenbestand abrufen
            lager_items_startseite = lagersystem.get_lagerbestand(
                barcode_filter=barcode_search_startseite, 
                ort_filter=ort_filter_startseite
            )

            # Tabelle anzeigen
            st.dataframe(lager_items_startseite, use_container_width=True, height=300)

        with tab2:
            st.subheader("🔍 Artikelübersicht")

            # Dropdown für Artikelnamen
            artikel_namen = lagersystem.get_artikel_namen()
            artikel_namen.insert(0, "Alle")  # Option für "Alle Artikel" hinzufügen
            selected_artikel = st.selectbox("🆔 Artikelname auswählen", artikel_namen)

            # Artikelbestand abrufen & nach Namen filtern
            artikel_anzahl = lagersystem.get_artikel_anzahl()
            if selected_artikel != "Alle":
                artikel_anzahl = artikel_anzahl[artikel_anzahl["Name"] == selected_artikel]

            # Tabelle mit Artikelübersicht anzeigen
            st.dataframe(artikel_anzahl, use_container_width=True, height=300)


    elif choice == "Lagersystem":
        st.subheader("📦 Lagerbestand & Verwaltung")

        tab1, tab2 = st.tabs(["📦 Lagerbestand", "⚙️ Aktionen"])

        # 📦 TAB 1: Lagerbestand im Lager anzeigen
        with tab1:
            st.subheader("📦 Verfügbare Medikamente im Lager")

            # Warnungen für abgelaufene Medikamente anzeigen
            warnungen = lagersystem.get_warnungen(ort_filter="Lager")
            if not warnungen.empty:
                st.warning("⚠️ Achtung: Es gibt abgelaufene Medikamente im Lager!")

            # Expander für die Barcode-Suche
            with st.expander("🔍 Lagerbestand durchsuchen"):
                barcode_search = st.text_input("🔎 Barcode suchen", key="barcode_search_lager")

            # Tabelle mit Lagerbestand
            lager_items = lagersystem.get_lagerbestand(barcode_filter=barcode_search, ort_filter="Lager")
            st.dataframe(lager_items, use_container_width=True, height=250)

        # ⚙️ TAB 2: Aktionen (Hinzufügen/Entfernen)
        with tab2:
            st.subheader("⚙️ Medikamentenverwaltung im Lager")

            # Expander für "Ware hinzufügen"
            with st.expander("➕ Ware hinzufügen"):
                st.subheader("📥 Neues Medikament ins Lager einfügen")
                barcode = st.text_input("📌 Barcode eingeben", key="barcode_add_lager")
                name = st.text_input("📋 Name des Medikaments", key="name_add_lager")
                verfallsdatum = st.date_input("🗓 Verfallsdatum wählen", key="date_add_lager")

                if st.button("✅ Medikament hinzufügen", key="btn_add_lager"):
                    if barcode and name and verfallsdatum:
                        message = lagersystem.ware_hinzufuegen(barcode, name, verfallsdatum.strftime('%Y-%m-%d'), ort="Lager")
                        if "Fehler" in message:
                            st.error(message)
                        else:
                            st.success(message)
                        st.rerun()

            # Expander für "Ware löschen"
            with st.expander("🗑 Ware löschen"):
                st.subheader("📤 Medikament aus dem Lager entfernen")
                barcode_remove = st.text_input("📌 Barcode des zu entfernenden Medikaments", key="barcode_remove_lager")

                if st.button("🗑 Medikament entfernen", key="btn_remove_lager"):
                    if barcode_remove:
                        message = lagersystem.ware_entfernen(barcode_remove)
                        if "Fehler" in message:
                            st.error(message)
                        else:
                            st.success(message)
                        st.rerun()


    elif choice == "Automat":
        st.subheader("🤖 Automatenbestand & Bestellungen")

        tab1, tab2, tab3 = st.tabs(["📦 Lagerbestand", "⚙️ Aktionen", "🛒 Bestellungen"])

        # 📦 TAB 1: Lagerbestand im Automaten anzeigen
        with tab1:
            st.subheader("📦 Verfügbare Medikamente im Automaten")

            # Warnungen für abgelaufene Medikamente
            warnungen = lagersystem.get_warnungen(ort_filter="Automat")
            if not warnungen.empty:
                st.warning("⚠️ Achtung: Es gibt abgelaufene Medikamente im Automaten!")

            
            # Layout für Suche & Filter im Automatenbestand
            col1, col2 = st.columns([2, 2])  
            with col1:
                barcode_search_automat = st.text_input("🔍 Barcode suchen", key="barcode_search_automat")
            with col2:
                belegte_kanaele = ["Alle"] + lagersystem.get_belegte_kanaele()
                kanal_filter = st.selectbox("📌 Kanal auswählen", belegte_kanaele, key="kanal_filter")


            # Tabelle mit Lagerbestand im Automaten nach Kanal gefiltert
            automat_items = lagersystem.get_lagerbestand(barcode_filter=barcode_search_automat, ort_filter="Automat")
            st.dataframe(automat_items, use_container_width=True, height=250)

        # ⚙️ TAB 2: Aktionen (Hinzufügen/Entfernen)
        with tab2:
            st.subheader("⚙️ Medikamentenverwaltung im Automaten")

            # Expander für "Ware zum Automaten hinzufügen"
            with st.expander("📤 Ware in den Automaten verschieben"):
                st.subheader("📥 Medikament in den Automaten verschieben")
                barcode_add = st.text_input("📌 Barcode der Ware eingeben", key="barcode_add_automat")

                if st.button("✅ Medikament in Automaten verschieben", key="btn_add_automat"):
                    if barcode_add:
                        message = lagersystem.ware_zum_automaten_hinzufuegen(barcode_add)
                        if "Fehler" in message:
                            st.error(message)
                        else:
                            st.success(message)
                        st.rerun()

            # Expander für "Ware aus Automaten entfernen"
            with st.expander("🗑 Ware aus Automaten entfernen"):
                st.subheader("📤 Medikament aus dem Automaten entfernen")
                barcode_remove = st.text_input("📌 Barcode der Ware eingeben", key="barcode_remove_automat")

                if st.button("🗑 Medikament entfernen", key="btn_remove_automat"):
                    if barcode_remove:
                        message = lagersystem.ware_aus_automaten_entfernen(barcode_remove)
                        if "Fehler" in message:
                            st.error(message)
                        else:
                            st.success(message)
                        st.rerun()

        # 🛒 TAB 3: Bestellungen & Warenkorb
        with tab3:
            st.subheader("🛒 Bestellungen & Warenkorb")
            barcode_bestellung = st.text_input("🔍 Barcode scannen", key="warenkorb_barcode")

            if st.button("➕ Medikament hinzufügen", key="btn_add_warenkorb"):
                if barcode_bestellung:
                    message = lagersystem.ware_zum_warenkorb_hinzufuegen(barcode_bestellung)
                    if "Fehler" in message:
                        st.error(message)
                    else:
                        st.success(message)
                    st.rerun()

            # Expander für Warenkorb
            with st.expander("🛒 Warenkorb anzeigen"):
                if st.session_state.warenkorb:
                    warenkorb_df = pd.DataFrame(st.session_state.warenkorb)
                    st.dataframe(warenkorb_df, use_container_width=True)

                    # Button zum Leeren des Warenkorbs
                    if st.button("🗑 Warenkorb leeren"):
                        st.session_state.warenkorb = []
                        st.success("Warenkorb geleert!")
                        st.rerun()

                    # Bestellung abschicken
                    if st.button("📦 Bestellung abschicken"):
                        message = lagersystem.bestellung_abschicken(st.session_state.kundennummer)
                        if "Fehler" in message:
                            st.error(message)
                        else:
                            st.success(message)
                        st.rerun()
                else:
                    st.info("Ihr Warenkorb ist leer.")

            # Expander für Bestellübersicht
            with st.expander("📋 Meine Bestellungen anzeigen"):
                bestellungen_df = lagersystem.get_bestellungen_gruppiert(st.session_state.kundennummer)

                if not bestellungen_df.empty:
                    st.write("### 📋 Bestellübersicht")
                    st.dataframe(bestellungen_df, use_container_width=True)

                    # Dropdown für Bestellstornierung
                    offene_bestellungen = bestellungen_df[bestellungen_df["Status"] == "Offen"]

                    if not offene_bestellungen.empty:
                        bestell_options = {f"Bestellung {row['Bestell-ID']}: {row['Medikamente']}": row['Bestell-ID']
                                        for _, row in offene_bestellungen.iterrows()}

                        selected_bestell_text = st.selectbox("📌 Bestellung zum Stornieren auswählen", list(bestell_options.keys()), key="bestell_storno")

                        if st.button("🗑 Bestellung stornieren", key="btn_storno"):
                            bestell_id = bestell_options[selected_bestell_text]
                            message = lagersystem.bestellung_stornieren(bestell_id, st.session_state.kundennummer)
                            if "Fehler" in message:
                                st.error(message)
                            else:
                                st.success(message)
                            st.rerun()
                    else:
                        st.info("Keine offenen Bestellungen vorhanden.")
                else:
                    st.info("Keine Bestellungen vorhanden.")



    elif choice == "Warnungen verwalten":
        st.subheader("Warnungen zu abgelaufenen Medikamenten")

        ort_filter_warnungen = st.selectbox("Ort filtern", ["Alle", "Lager", "Automat"], index=0)
        warnungen = lagersystem.get_warnungen(ort_filter=ort_filter_warnungen if ort_filter_warnungen != "Alle" else None)

        if warnungen.empty:
            st.success("Keine abgelaufenen Medikamente!")
        else:
            st.dataframe(warnungen, use_container_width=True)


