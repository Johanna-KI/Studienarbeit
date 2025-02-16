import streamlit as st
import pandas as pd
import sqlite3
import bcrypt
import time
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
        print(f"Datenbankinitialisierung: {time.time() - start_time:.5f} Sekunden")

    def _initialize_database(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS lagerbestand (
                barcode TEXT PRIMARY KEY,
                name TEXT,
                menge INTEGER,
                verfallsdatum TEXT,
                ort TEXT DEFAULT 'Lager'
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
    
    def ware_hinzufuegen(self, barcode, name, verfallsdatum, ort='Lager'):
        self.cursor.execute("SELECT * FROM lagerbestand WHERE barcode = ?", (barcode,))
        row = self.cursor.fetchone()
        if row:
            return f"Fehler: Der Barcode {barcode} existiert bereits im Lagerbestand!"
        else:
            self.cursor.execute("INSERT INTO lagerbestand (barcode, name, menge, verfallsdatum, ort) VALUES (?, ?, 1, ?, ?)", (barcode, name, verfallsdatum, ort))
            self.db_conn.commit()
            return f"Erfolg: 1 Einheit von {name} zum {ort} hinzugefügt."

    def ware_entfernen(self, barcode):
        self.cursor.execute("SELECT * FROM lagerbestand WHERE barcode = ?", (barcode,))
        row = self.cursor.fetchone()
        if row:
            self.cursor.execute("DELETE FROM lagerbestand WHERE barcode = ?", (barcode,))
            self.cursor.execute("DELETE FROM warnungen WHERE barcode = ?", (barcode,))  # Warnung automatisch löschen
            self.db_conn.commit()
            return f"Erfolg: Ware mit Barcode {barcode} aus dem Lager entfernt."
        else:
            return f"Fehler: Barcode {barcode} nicht im Lagerbestand gefunden!"

    def get_lagerbestand(self, barcode_filter=None, ort_filter=None):
        self._pruefe_warnungen()
        
        query = "SELECT barcode, name, menge, verfallsdatum, ort FROM lagerbestand WHERE 1=1"
        params = []

        if ort_filter in ["Lager", "Automat"]:
            query += " AND ort = ?"
            params.append(ort_filter)

        if barcode_filter:
            query += " AND barcode LIKE ?"
            params.append(f"%{barcode_filter}%")

        self.cursor.execute(query, params)
        data = self.cursor.fetchall()

        df = pd.DataFrame(data, columns=["Barcode", "Name", "Menge", "Verfallsdatum", "Ort"])
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
        self.cursor.execute("SELECT * FROM lagerbestand WHERE barcode = ?", (barcode,))
        row = self.cursor.fetchone()

        if row:
            self.cursor.execute("UPDATE lagerbestand SET ort = 'Automat' WHERE barcode = ?", (barcode,))
            self.db_conn.commit()
            self._pruefe_warnungen()  # Warnungen aktualisieren
            return f"Erfolg: Ware mit Barcode {barcode} wurde in den Automaten verschoben."
        else:
            return f"Fehler: Artikel mit Barcode {barcode} existiert nicht im Lagerbestand!"

    
    def ware_aus_automaten_entfernen(self, barcode):
        self.cursor.execute("SELECT * FROM lagerbestand WHERE barcode = ? AND ort = 'Automat'", (barcode,))
        row = self.cursor.fetchone()

        if row:
            self.cursor.execute("UPDATE lagerbestand SET ort = 'Lager' WHERE barcode = ?", (barcode,))
            self.db_conn.commit()
            self._pruefe_warnungen()  # Warnungen aktualisieren
            return f"Erfolg: Ware mit Barcode {barcode} wurde zurück ins Lager verschoben."
        else:
            return f"Fehler: Der Artikel mit Barcode {barcode} ist nicht im Automaten!"
        
    def hash_password(self, password):
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def verify_password(self, password, hashed):
        return bcrypt.checkpw(password.encode(), hashed.encode())

    def generate_kundennummer(self):
        return str(random.randint(10000000, 99999999))

    def register_user(self, username, password):
        kundennummer = self.generate_kundennummer()
        hashed_pw = self.hash_password(password)

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
                st.rerun()
            else:
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
                    st.rerun()
                else:
                    st.error("⚠️ Benutzername bereits vergeben!")
            else:
                st.error("⚠️ Bitte alle Felder ausfüllen!")

    st.markdown("</div>", unsafe_allow_html=True)


# **Sidebar: Kundennummer & Logout**
if st.session_state.authenticated:
    with st.sidebar:
        # Menü erstellen
        menu = ["Startseite", "Lagersystem", "Automat", "Warnungen verwalten"]
        choice = st.radio("Wählen Sie das System", menu)

        # Trennlinie
        st.markdown("---")

        # Kundennummer weiter unten anzeigen
        st.markdown("<br><br><br><br><br><br><br><br><br>", unsafe_allow_html=True)  # Abstand einfügen
        st.markdown(f"**Kundennummer:** `{st.session_state.get('kundennummer', 'Nicht gesetzt')}`")

        # Logout-Button
        if st.button("🚪 Abmelden", help="Klicken Sie hier, um sich abzumelden", use_container_width=True, key="logout_button"):
            st.session_state.authenticated = False
            st.session_state.kundennummer = None
            st.rerun()
    st.title("Lagersystem für Medikamente")
    
    if choice == "Startseite":
        st.subheader("Medikamentübersicht")
        view_option = st.selectbox("Ansicht auswählen", ["Gesamtübersicht", "Artikelübersicht"], index=0)
        
        if view_option == "Gesamtübersicht":
            warnungen = lagersystem.get_warnungen()
            if not warnungen.empty:
                st.warning("Es gibt abgelaufene Medikamente! Überprüfen Sie den Reiter 'Warnungen verwalten'.")
            col1, col2 = st.columns([2, 2])  # Geteiltes Layout für Suche & Filter
            with col1:
                barcode_search_startseite = st.text_input("Barcode suchen")
            with col2:
                ort_filter_startseite = st.selectbox("Ort filtern", ["Alle", "Lager", "Automat"], index=0)

            lager_items_startseite = lagersystem.get_lagerbestand(
                barcode_filter=barcode_search_startseite, 
                ort_filter=ort_filter_startseite
            )
            st.dataframe(lager_items_startseite, use_container_width=True, height=200)

        elif view_option == "Artikelübersicht":

            # Dropdown für Artikelnamen
            artikel_namen = lagersystem.get_artikel_namen()
            artikel_namen.insert(0, "Alle")  # Option für "Alle Artikel" hinzufügen
            selected_artikel = st.selectbox("Artikelname auswählen", artikel_namen)

            # Artikelbestand abrufen & nach Namen filtern
            artikel_anzahl = lagersystem.get_artikel_anzahl()
            
            if selected_artikel != "Alle":
                artikel_anzahl = artikel_anzahl[artikel_anzahl["Name"] == selected_artikel]

            st.dataframe(artikel_anzahl, use_container_width=True, height=200)


    elif choice == "Lagersystem":
        st.subheader("Lagerbestand")

        warnungen = lagersystem.get_warnungen(ort_filter="Lager")
        if not warnungen.empty:
            st.warning("Achtung: Es gibt abgelaufene Medikamente im Lager!")


        barcode_search = st.text_input("Barcode suchen")

        lager_items = lagersystem.get_lagerbestand(barcode_filter=barcode_search, ort_filter="Lager")
        st.dataframe(lager_items, use_container_width=True, height=200)

        action = st.selectbox("Aktion auswählen", ["Ware hinzufügen", "Ware löschen"])

        if action == "Ware hinzufügen":
            st.subheader("Ware hinzufügen")
            barcode = st.text_input("Barcode")
            name = st.text_input("Name")
            verfallsdatum = st.date_input("Verfallsdatum")

            if st.button("Hinzufügen"):
                if barcode and name and verfallsdatum:
                    message = lagersystem.ware_hinzufuegen(barcode, name, verfallsdatum.strftime('%Y-%m-%d'), ort="Lager")
                    st.success(message)
                    st.rerun()

        elif action == "Ware löschen":
            st.subheader("Ware löschen")
            barcode_remove = st.text_input("Barcode zum Entfernen")
            if st.button("Entfernen"):
                if barcode_remove:
                    message = lagersystem.ware_entfernen(barcode_remove)
                    if "Fehler" in message:
                        st.error(message)
                    else:
                        st.success(message)
                    st.rerun()


    elif choice == "Automat":
        st.subheader("Automatenbestand")

        warnungen = lagersystem.get_warnungen(ort_filter="Automat")
        if not warnungen.empty:
            st.warning("Achtung: Es gibt abgelaufene Medikamente im Automaten!")

        barcode_search_automat = st.text_input("Barcode suchen")
        automat_items = lagersystem.get_lagerbestand(barcode_filter=barcode_search_automat, ort_filter="Automat")
        st.dataframe(automat_items, use_container_width=True, height=200)

        action = st.selectbox("Aktion auswählen", ["Ware zum Automaten hinzufügen", "Ware aus Automaten entfernen"])

        if action == "Ware zum Automaten hinzufügen":
            st.subheader("Medikament in den Automaten verschieben")
            barcode_add = st.text_input("Barcode der Ware")
            if st.button("Hinzufügen"):
                if barcode_add:
                    message = lagersystem.ware_zum_automaten_hinzufuegen(barcode_add)
                    if "Fehler" in message:
                        st.error(message)
                    else:
                        st.success(message)
                    st.rerun()

        elif action == "Ware aus Automaten entfernen":
            st.subheader("Medikament aus dem Automaten entfernen")
            barcode_remove = st.text_input("Barcode der Ware")
            if st.button("Entfernen"):
                if barcode_remove:
                    message = lagersystem.ware_aus_automaten_entfernen(barcode_remove)
                    if "Fehler" in message:
                        st.error(message)
                    else:
                        st.success(message)
                    st.rerun()

    elif choice == "Warnungen verwalten":
        st.subheader("Warnungen zu abgelaufenen Medikamenten")

        ort_filter_warnungen = st.selectbox("Ort filtern", ["Alle", "Lager", "Automat"], index=0)
        warnungen = lagersystem.get_warnungen(ort_filter=ort_filter_warnungen if ort_filter_warnungen != "Alle" else None)

        if warnungen.empty:
            st.success("Keine abgelaufenen Medikamente!")
        else:
            st.dataframe(warnungen, use_container_width=True)


