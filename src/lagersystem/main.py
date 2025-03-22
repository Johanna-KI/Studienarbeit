import streamlit as st
import pandas as pd
import bcrypt
import time
import sqlite3
import csv
import random
from datetime import datetime
from admin import Admin
from anmeldung import Anmeldung
from automat import Automat
from lager import Lager
from datenbank import Datenbank
from warnung import Warnung
import traceback


# 🔴 Muss die erste Streamlit-Funktion sein!
st.set_page_config(page_title="Lagersystem für Medikamente", layout="centered")



admin = Admin()
anmeldung = Anmeldung()
lager = Lager()
automat = Automat()
datenbank = Datenbank()
warnung = Warnung()     


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
    st.session_state.role = None

# **Login- oder Registrierungsanzeige**
if not st.session_state.authenticated:

        # **Überschrift in der Box**
        st.markdown('<p class="login-title">Lagersystem Anmeldung</p>', unsafe_allow_html=True)

        tab1, tab2, tab3 = st.tabs(["🔑 Benutzer-Login", "🆕 Registrierung", "🔐 Admin-Login"])

        # **Benutzer-Login**
        with tab1:
            username = st.text_input("Benutzername", key="login_username")
            password = st.text_input("Passwort", type="password", key="login_password")

            if st.button("🔑 Anmelden"):
                user_data = anmeldung.get_user(username)
                if user_data and anmeldung.verify_password(password, user_data[1]):
                    st.session_state.authenticated = True
                    st.session_state.kundennummer = user_data[0]
                    st.session_state.username = username
                    datenbank.log_aktion("✅ User-Login erfolgreich")
                    st.toast("✅ Erfolgreich angemeldet!", icon="✅")
                    time.sleep(0.75)
                    st.rerun()
                else:
                    datenbank.log_aktion("🚫 User-Login fehlgeschlagen")
                    st.toast("🚫 Falscher Benutzername oder Passwort!", icon="🚫")

        # **Benutzer-Registrierung**
        with tab2:
            new_username = st.text_input("Neuer Benutzername", key="register_username")
            new_password = st.text_input("Neues Passwort", type="password", key="register_password")

            if st.button("🆕 Registrieren"):
                if new_username and new_password:
                    kundennummer, message = anmeldung.register_user(new_username, new_password)
                    if kundennummer:
                        st.toast(f"✅ Erfolgreich registriert! Ihre Kundennummer: {kundennummer}", icon="✅")
                        st.session_state.authenticated = True
                        st.session_state.kundennummer = kundennummer
                        st.session_state.username = new_username
                        datenbank.log_aktion("✅ Registrierung erfolgreich")
                        time.sleep(0.75)
                        st.rerun()
                    else:
                        st.toast(message, icon="🚫")  # 🚫 Fehlermeldung anzeigen
                else:
                    datenbank.log_aktion("🚫 Registrierung fehlgeschlagen")
                    st.toast("⚠️ Bitte alle Felder ausfüllen!", icon="⚠️")

        # **Admin-Login**
        with tab3:
            admin_username = st.text_input("Admin Benutzername")
            admin_password = st.text_input("Admin Passwort", type="password")

            if st.button("🔐 Admin-Anmelden"):
                """
                Verifiziert den Admin-Zugang mit Benutzername und Passwort.
                Nur Benutzer mit Admin-Rechten können sich erfolgreich anmelden.
                """
                admin_data = anmeldung.get_user(admin_username)
                if admin_data and bcrypt.checkpw(admin_password.encode(), admin_data[1].encode()) and admin_data[2] == "admin":
                    st.session_state.authenticated = True
                    st.session_state.kundennummer = admin_data[0]
                    st.session_state.username = admin_username
                    st.session_state.role = "admin"
                    datenbank.log_aktion("✅ Admin-Login erfolgreich")
                    st.toast("✅ Erfolgreich als Admin angemeldet!", icon="✅")
                    time.sleep(0.75)
                    st.rerun()
                else:
                    datenbank.log_aktion("🚫 Admin-Login fehlgeschlagen")
                    st.toast("🚫 Falscher Admin-Benutzername oder Passwort!", icon="🚫")

elif st.session_state.authenticated and st.session_state.role == "admin":

        st.sidebar.markdown("""
        <h3 style='text-align: center;'>📌 Admin Navigation</h3>
            <hr style='border: 1px solid #ddd; margin: 10px 0;'>
        """, unsafe_allow_html=True)

        admin_menu = {
            "📋 Bestellungen": "📋 Bestellungen",
            "📜 Logdatei": "📜 Logdatei",
            "👥 Benutzerverwaltung": "👥 Benutzerverwaltung"
        }
        choice = st.sidebar.radio("**Wählen Sie eine Option:**", list(admin_menu.keys()), format_func=lambda x: admin_menu[x])

        # **Trennlinie mit zusätzlichem Abstand nach unten**
        st.sidebar.markdown("<hr style='border: 1px solid #ddd; margin: 0px 0;'>", unsafe_allow_html=True)

        # **Zentrierte Benutzer-Info weiter unten**
        st.sidebar.markdown("""
            <div style='text-align: center;'>
                <span style='font-size: 25px;'>🧑‍💼</span>
                <h4 style='margin-top: 5px;'>**Admin-Kundennummer:**</h4>
                <p style='font-size: 18px; font-weight: bold; color: #003366;'>
                    {kundennummer}
                </p>
            </div>
        """.format(kundennummer=st.session_state.get('kundennummer', 'Nicht gesetzt')), unsafe_allow_html=True)

        # **Zusätzlicher Abstand für ein aufgeräumtes Layout**
        st.sidebar.markdown("<hr style='border: 1px solid #ddd; margin: 30px 0;'><br>", unsafe_allow_html=True)

        # **Logout-Button am unteren Rand mit Icon**
        if st.sidebar.button("🚪 Abmelden", help="Sicher abmelden", use_container_width=True, key="logout_button"):
            st.session_state.authenticated = False
            datenbank.log_aktion("✅ Admin-Logout erfolgreich")
            st.session_state.kundennummer = None
            st.session_state.username = None
            st.session_state.role = None
            st.toast("🚪 Erfolgreich abgemeldet!", icon="✅")
            time.sleep(0.75)
            st.rerun()

        if admin_menu[choice] == "📋 Bestellungen":
            tab1, tab2 = st.tabs(["📋 Übersicht Bestellungen", "✅ Offene Bestellungen genehmigen"]) 
            
            # 📋 TAB 1: Alle Bestellungen anzeigen
            with tab1:
                st.subheader("📋 Alle Bestellungen anzeigen")

                with st.expander("🔍 Bestellungen filtern", expanded=True):
                    col1, col2 = st.columns(2)

                    with col1:
                        bestell_id_filter = st.text_input("🔎 Nach Bestell-ID suchen:", help="Geben Sie eine Bestell-ID ein, um gezielt zu suchen.")

                    with col2:
                        status_optionen = ["Alle", "Offen", "Genehmigt", "Storniert"]
                        ausgewählter_status = st.selectbox("📦 Status filtern:", status_optionen, help="Filtern Sie Bestellungen nach Status.")

                # 🔎 Datenbankabfrage für gefilterte Bestellungen
                status_filter = ("Offen", "Genehmigt", "Storniert") if ausgewählter_status == "Alle" else (ausgewählter_status,)
                bestellungen = admin.get_bestellungen(bestell_id_filter=bestell_id_filter, status=status_filter)

                if not bestellungen.empty:
                    st.dataframe(bestellungen, use_container_width=True)
                    datenbank.log_aktion(f"📋 Admin hat Bestellungen gefiltert: Bestell-ID: {bestell_id_filter}, Status: {ausgewählter_status}")
                else:
                    st.error("🚫 Keine Bestellungen für die gewählten Kriterien gefunden.")
                    st.toast("🚫 Keine Bestellungen für die gewählten Kriterien gefunden!", icon="🚫")
                    datenbank.log_aktion(f"🚫 Keine Bestellungen gefunden für Bestell-ID: {bestell_id_filter}, Status: {ausgewählter_status}")

            # ✅ TAB 2: Offene Bestellungen genehmigen
            with tab2:
                st.subheader("✅ Offene Bestellungen genehmigen")

                bestellungen = admin.get_bestellungen(status=("Offen",))

                if not bestellungen.empty:
                    st.dataframe(bestellungen, use_container_width=True)

                    bestell_id = st.selectbox("📦 Bestellung auswählen", bestellungen["Bestell-ID"])

                    
                    if st.button("✔️ Genehmigen", use_container_width=True):
                            admin.update_bestellstatus(bestell_id, "Genehmigt")
                            st.toast(f"✅ Bestellung {bestell_id} genehmigt!", icon="✅")
                            datenbank.log_aktion(f"✅ Bestellung {bestell_id} wurde genehmigt")
                            time.sleep(0.75)
                            st.rerun()

                else:
                    st.error("🚫 Keine offenen Bestellungen vorhanden.")
                    st.toast("🚫 Keine offenen Bestellungen im System!", icon="🚫")
                    datenbank.log_aktion("🚫 Keine offenen Bestellungen gefunden.")



        elif admin_menu[choice] == "📜 Logdatei":
            st.subheader("📜 Logdatei einsehen")

            # 🔍 Expander für die Filteroptionen
            with st.expander("🔍 Logdatei filtern", expanded=True):
                col1, col2, col3 = st.columns([2, 1, 1])

                with col1:
                    selected_date = st.date_input(
                        "📅 Wählen Sie ein Datum aus:", 
                        datetime.today(), 
                        key="log_date_filter",
                        help="Wählen Sie das Datum, für das die Logeinträge angezeigt werden sollen."
                    )

                with col2:
                    start_time = st.time_input(
                        "⏰ Startzeit wählen", 
                        value=datetime.strptime("00:00", "%H:%M").time(), 
                        key="log_start_time",
                        help="Startzeit des gewünschten Zeitraums auswählen."
                    )

                with col3:
                    end_time = st.time_input(
                        "⏰ Endzeit wählen", 
                        value=datetime.strptime("23:59", "%H:%M").time(), 
                        key="log_end_time",
                        help="Endzeit des gewünschten Zeitraums auswählen."
                    )

            # **Daten aus Logdatei abrufen**
            logs = admin.get_logdatei()

            if logs.empty:
                st.info("🔍 Keine Logeinträge vorhanden.")
                st.toast("ℹ️ Es sind keine Logeinträge vorhanden.", icon="ℹ️")
                datenbank.log_aktion("🚫 Keine Logeinträge gefunden.")
            else:
                # **Datum in das passende Format umwandeln**
                selected_date_str = selected_date.strftime('%Y-%m-%d')

                # **Logdatei nach Datum filtern**
                filtered_logs = logs[logs["Zeitstempel"].str.startswith(selected_date_str)]

                if not filtered_logs.empty:
                    # 🕒 Zeitstempel umwandeln in Uhrzeit-Format für weitere Filterung
                    filtered_logs["Uhrzeit"] = pd.to_datetime(filtered_logs["Zeitstempel"]).dt.time

                    # 🕒 Logeinträge nach Start- und Endzeit filtern
                    filtered_logs = filtered_logs[
                        (filtered_logs["Uhrzeit"] >= start_time) & 
                        (filtered_logs["Uhrzeit"] <= end_time)
                    ]

                    # 📊 Gefilterte Logs anzeigen
                    if not filtered_logs.empty:
                        st.dataframe(filtered_logs.drop(columns=["Uhrzeit"]), use_container_width=True)
                        st.toast(f"📜 {len(filtered_logs)} Logeinträge für {selected_date_str} zwischen {start_time} - {end_time} gefunden!", icon="📜")
                        datenbank.log_aktion(f"📜 Admin hat Logeinträge für {selected_date_str} von {start_time} bis {end_time} aufgerufen.")
                    else:
                        st.warning(f"🚫 Keine Logeinträge für {selected_date_str} zwischen {start_time} und {end_time} gefunden.")
                        st.toast(f"🚫 Keine Logeinträge im gewählten Zeitraum!", icon="⚠️")
                        datenbank.log_aktion(f"🚫 Keine Logeinträge für {selected_date_str} zwischen {start_time} und {end_time} gefunden.")



        elif admin_menu[choice] == "👥 Benutzerverwaltung":
            st.subheader("👥 Benutzerverwaltung")

            users_df = admin.get_users()

            if users_df.empty:
                st.info("🔍 Keine Benutzer gefunden.")
                st.toast("ℹ️ Es sind keine Benutzer im System registriert.", icon="ℹ️")
                datenbank.log_aktion("🚫 Keine Benutzer im System gefunden.")
            else:
                with st.expander("🔍 Benutzername suchen", expanded=True):
                    username_search = st.text_input("🔍 Benutzername eingeben:", help="Geben Sie einen Benutzernamen ein, um nach einem bestimmten Benutzer zu suchen.")

                filtered_users = admin.get_users(username_filter=username_search)

                if not filtered_users.empty:
                    st.dataframe(filtered_users, use_container_width=True)
                    datenbank.log_aktion(f"👥 Admin hat Benutzer gesucht: {username_search}")
                else:
                    st.warning("🚫 Keine Benutzer mit diesem Namen gefunden.")
                    st.toast("🚫 Kein Benutzer mit diesem Namen gefunden!", icon="⚠️")
                    datenbank.log_aktion(f"🚫 Benutzername nicht gefunden: {username_search}")


else:
           
        if "warenkorb" not in st.session_state:
            st.session_state.warenkorb = []

        with st.sidebar:
            # **Menü mit Icons und besserer Abtrennung**
            st.markdown("""
                <h3 style='text-align: center;'>📌 Navigation</h3>
                <hr style='border: 1px solid #ddd; margin: 10px 0;'>
            """, unsafe_allow_html=True)

            menu = {
                "🏠 Startseite": "🏠 Startseite",
                "📦 Lagersystem": "📦 Lagersystem",
                "🤖 Automat": "🤖 Automat",
                "⚠️ Warnungen verwalten": "⚠️ Warnungen verwalten"
            }
            choice = st.radio("**Wählen Sie eine Option:**", list(menu.keys()), format_func=lambda x: menu[x])

            # **Trennlinie mit zusätzlichem Abstand nach unten**
            st.markdown("<hr style='border: 1px solid #ddd; margin: 0px 0;'>", unsafe_allow_html=True)

            # **Zentrierte Benutzer-Info weiter unten**
            st.markdown("""
                <div style='text-align: center;'>
                    <span style='font-size: 25px;'>🧑‍💼</span>
                    <h4 style='margin-top: 5px;'>**Kundennummer:**</h4>
                    <p style='font-size: 18px; font-weight: bold; color: #003366;'>
                        {kundennummer}
                    </p>
                </div>
            """.format(kundennummer=st.session_state.get('kundennummer', 'Nicht gesetzt')), unsafe_allow_html=True)

            # **Zusätzlicher Abstand für ein aufgeräumtes Layout**
            st.markdown("<hr style='border: 1px solid #ddd; margin: 30px 0;'><br>", unsafe_allow_html=True)

            # **Logout-Button am unteren Rand mit Icon**
            if st.button("🚪 Abmelden", help="Klicken Sie hier, um sich sicher abzumelden", use_container_width=True, key="logout_button"):
                st.session_state.authenticated = False
                datenbank.log_aktion("✅ User-Logout erfolgreich")
                st.session_state.kundennummer = None
                st.session_state.username = None
                st.session_state.role = None
                st.rerun()


            st.markdown("</div>", unsafe_allow_html=True)



        
        if menu[choice] == "🏠 Startseite":

            tab1, tab2 = st.tabs(["📋 Gesamtübersicht", "🔍 Artikelübersicht"])

            ### 📋 TAB 1: Gesamtübersicht der Medikamente
            with tab1:
                st.subheader("📋 Gesamtübersicht der Medikamente")

                # 🔔 Warnungen für abgelaufene Medikamente anzeigen
                warnungen = warnung.get_warnungen()
                if not warnungen.empty:
                    st.warning("⚠️ Es gibt abgelaufene Medikamente! Überprüfen Sie den Reiter 'Warnungen verwalten'.")
                    datenbank.log_aktion("⚠️ Benutzer hat die Gesamtübersicht aufgerufen - Abgelaufene Medikamente vorhanden")

                # 🔍 Expander für Suche & Filteroptionen
                with st.expander("🔍 Such- & Filteroptionen anzeigen", expanded=True):
                    col1, col2 = st.columns([2, 2])

                    with col1:
                        barcode_search_startseite = st.text_input(
                            "🔍 Barcode suchen", 
                            help="Scannen oder geben Sie einen Barcode ein, um gezielt nach Medikamenten zu suchen."
                        )

                    with col2:
                        ort_filter_startseite = st.selectbox(
                            "📍 Ort filtern", 
                            ["Alle", "Lager", "Automat"], 
                            index=0, 
                            help="Wählen Sie einen Standort aus, um die Medikamentensuche einzugrenzen."
                        )

                # 📊 Medikamentenbestand abrufen
                lager_items_startseite = lager.get_lagerbestand(
                    barcode_filter=barcode_search_startseite, 
                    ort_filter=ort_filter_startseite
                )

                # 🚫 Falls keine Medikamente gefunden werden
                if lager_items_startseite.empty:
                    st.error("🚫 Keine Medikamente gefunden! Bitte überprüfen Sie Ihre Suchkriterien.")
                    datenbank.log_aktion(f"🔍 Keine Medikamente gefunden für Filter - Barcode: {barcode_search_startseite}, Ort: {ort_filter_startseite}")
                else:
                    st.dataframe(lager_items_startseite, use_container_width=True, height=300)
                    datenbank.log_aktion(f"📊 Benutzer hat Medikamente gefiltert - Barcode: {barcode_search_startseite}, Ort: {ort_filter_startseite}")

            ### 🔍 TAB 2: Artikelübersicht
            with tab2:
                st.subheader("🔍 Artikelübersicht")

                # 📌 Expander für Filteroptionen
                with st.expander("🔍 Artikel filtern", expanded=True):
                    col1 = st.columns(1)[0]  # Bessere Strukturierung der Auswahl

                    with col1:
                        artikel_namen = lager.get_artikel_namen()
                        artikel_namen.insert(0, "Alle")  # "Alle" als Standardoption
                        selected_artikel = st.selectbox(
                            "🆔 Artikelname auswählen", 
                            artikel_namen, 
                            help="Wählen Sie einen spezifischen Artikel oder 'Alle', um alle Artikel anzuzeigen."
                        )

                # 📊 Artikelbestand abrufen & nach Namen filtern
                artikel_anzahl = lager.get_artikel_anzahl()
                if selected_artikel != "Alle":
                    artikel_anzahl = artikel_anzahl[artikel_anzahl["Name"] == selected_artikel]

                # 🚫 Falls keine Artikel gefunden wurden
                if artikel_anzahl.empty:
                    st.error("🚫 Keine Artikel gefunden! Bitte überprüfen Sie Ihre Auswahl.")
                    datenbank.log_aktion(f"🔍 Keine Artikel gefunden für Auswahl: {selected_artikel}")
                else:
                    st.dataframe(artikel_anzahl, use_container_width=True, height=300)
                    datenbank.log_aktion(f"📊 Benutzer hat Artikel gefiltert: {selected_artikel}")




        elif menu[choice] == "📦 Lagersystem":

            tab1, tab2 = st.tabs(["📦 Lagerbestand", "⚙️ Aktionen"])

            # 📦 TAB 1: Lagerbestand im Lager anzeigen
            with tab1:
                st.subheader("📦 Verfügbare Medikamente im Lager")

                # 🔔 Warnungen für abgelaufene Medikamente anzeigen
                warnungen = warnung.get_warnungen(ort_filter="Lager")
                if not warnungen.empty:
                    st.warning("⚠️ Achtung: Es gibt abgelaufene Medikamente im Lager!")
                    datenbank.log_aktion("⚠️ Benutzer hat Lagerbestand aufgerufen - Abgelaufene Medikamente vorhanden")

                # 🔍 Expander für Barcode-Suche & Filter
                with st.expander("🔍 Lagerbestand durchsuchen", expanded=True):
                    st.write("Nutzen Sie die Suchfunktion, um gezielt nach Medikamenten zu filtern.")
                    

                    barcode_search = st.text_input(
                            "🔍 Barcode eingeben", 
                            key="barcode_search_lager",
                            help="Scannen oder geben Sie einen Barcode ein, um ein Medikament zu finden."
                        )
                        

                # 📊 Lagerbestand abrufen
                lager_items = lager.get_lagerbestand(
                    barcode_filter=barcode_search, 
                    ort_filter = "Lager"
                )

                # 🚫 Falls keine Medikamente gefunden werden
                if lager_items.empty:
                    st.error("🚫 Keine Medikamente gefunden.")
                    datenbank.log_aktion(f"🔍 Keine Medikamente gefunden - Barcode: {barcode_search}")
                else:
                    st.dataframe(lager_items, use_container_width=True, height=300)
                    datenbank.log_aktion(f"📊 Benutzer hat Lagerbestand gefiltert - Barcode: {barcode_search}")

            # ⚙️ TAB 2: Aktionen (Hinzufügen/Entfernen)
            with tab2:
                st.subheader("⚙️ Medikamentenverwaltung im Lager")

                # ➕ Expander für "Ware hinzufügen"
                with st.expander("➕ Ware hinzufügen", expanded=True):
                    st.write("Hier können Sie ein neues Medikament in den Lagerbestand aufnehmen. Füllen Sie die folgenden Felder aus:")

                    col1, col2, col3 = st.columns([2, 2, 2])

                    with col1:
                        barcode = st.text_input(
                            "📌 Barcode eingeben", 
                            key="barcode_add_lager",
                            help="Scannen oder geben Sie den Barcode des Medikaments ein."
                        )

                    with col2:
                        name = st.text_input(
                            "📋 Name des Medikaments", 
                            key="name_add_lager",
                            help="Geben Sie den vollständigen Namen des Medikaments ein."
                        )

                    with col3:
                        verfallsdatum = st.date_input(
                            "🗓 Verfallsdatum wählen", 
                            key="date_add_lager",
                            help="Wählen Sie das Mindesthaltbarkeitsdatum des Medikaments."
                        )

                    # ✅ Button für das Hinzufügen (zentriert neben Eingabefelder)
                    if st.button("✅ Medikament hinzufügen", key="btn_add_lager", use_container_width=True):
                            if barcode and name and verfallsdatum:
                                message = lager.ware_hinzufuegen(barcode, name, verfallsdatum.strftime('%Y-%m-%d'), ort="Lager")

                                if "Fehler" in message:
                                    st.toast(f" {message}", icon="🚫")
                                    datenbank.log_aktion(f"🚫 Fehler beim Hinzufügen von {name} - {message}")
                                else:
                                    st.toast(f"✅ Medikament erfolgreich hinzugefügt!", icon="✅")
                                    datenbank.log_aktion(f"✅ Medikament {name} wurde erfolgreich hinzugefügt.")

                                time.sleep(0.75)  # ⏳ Kurzes Delay für UI-Aktualisierung
                                st.rerun()

                # 🗑 Expander für "Ware entfernen"
                with st.expander("🗑 Ware entfernen", expanded=True):
                    st.write("Geben Sie den Barcode eines Medikaments ein, um es aus dem Lagerbestand zu entfernen.")

                    barcode_remove = st.text_input(
                            "📌 Barcode des zu entfernenden Medikaments", 
                            key="barcode_remove_lager",
                            help="Scannen oder geben Sie den Barcode des zu entfernenden Medikaments ein."
                        )


                    if st.button("🗑 Medikament entfernen", key="btn_remove_lager", use_container_width=True):
                            if barcode_remove:
                                message = lager.ware_entfernen(barcode_remove)

                                if "Fehler" in message:
                                    st.toast(f" {message}", icon="🚫")
                                    datenbank.log_aktion(f"🚫 Fehler beim Entfernen von Medikament mit Barcode {barcode_remove} - {message}")
                                else:
                                    st.toast(f"✅ Medikament erfolgreich entfernt!", icon="✅")
                                    datenbank.log_aktion(f"✅ Medikament mit Barcode {barcode_remove} erfolgreich entfernt.")

                                time.sleep(0.75)
                                st.rerun()





        elif menu[choice] == "🤖 Automat":

            tab1, tab2, tab3 = st.tabs(["📦 Automatenbestand", "⚙️ Aktionen", "🛒 Bestellungen"])

            # 📦 TAB 1: Lagerbestand im Automaten anzeigen
            with tab1:
                st.subheader("📦 Verfügbare Medikamente im Automaten")

                # 🔔 Warnungen für abgelaufene Medikamente anzeigen
                warnungen = warnung.get_warnungen(ort_filter="Automat")
                if not warnungen.empty:
                    st.warning("⚠️ Achtung: Es gibt abgelaufene Medikamente im Automaten!")
                    datenbank.log_aktion("⚠️ Benutzer hat Automatenbestand aufgerufen - Abgelaufene Medikamente vorhanden")

                # 🔍 Expander für Suche & Filteroptionen
                with st.expander("🔍 Filter- und Suchoptionen ", expanded=True):
                    st.write("Verwenden Sie die untenstehenden Filter, um gezielt nach Medikamenten im Automaten zu suchen.")

                    col1, col2 = st.columns([2, 2])

                    with col1:
                        barcode_search_automat = st.text_input(
                            "🔍 Barcode eingeben oder scannen",
                            key="barcode_search_automat",
                            help="Geben Sie einen Barcode ein oder scannen Sie ihn, um gezielt nach einem Medikament zu suchen."
                        )

                    with col2:
                        belegte_kanaele = ["Alle"] + automat.get_belegte_kanaele()
                        kanal_filter = st.selectbox(
                            "📌 Kanal auswählen",
                            belegte_kanaele,
                            key="kanal_filter",
                            help="Wählen Sie einen spezifischen Kanal, um die Suche einzuschränken."
                        )

                # 📊 Tabelle mit Lagerbestand im Automaten abrufen
                automat_items = lager.get_lagerbestand(
                    barcode_filter=barcode_search_automat,
                    ort_filter="Automat"
                )

                # 🚫 Falls keine Medikamente gefunden werden
                if automat_items.empty:
                    st.error("🚫 Keine Medikamente im Automaten gefunden.")
                    datenbank.log_aktion(f"🔍 Keine Medikamente im Automaten gefunden - Filter: {barcode_search_automat}, Kanal: {kanal_filter}")
                else:
                    st.dataframe(automat_items, use_container_width=True, height=250)
                    datenbank.log_aktion(f"📊 Benutzer hat Automatenbestand gefiltert - Barcode: {barcode_search_automat}, Kanal: {kanal_filter}")

            # ⚙️ TAB 2: Aktionen (Hinzufügen/Entfernen)
            with tab2:
                st.subheader("⚙️ Medikamentenverwaltung im Automaten")

                # 🔄 Layout für eine moderne UI
                col1, col2 = st.columns([1, 1])

                # 📤 Expander für "Ware zum Automaten hinzufügen"
                with col1:
                    with st.expander("📤 Ware in den Automaten verschieben", expanded=True):
                        st.write("Fügen Sie ein Medikament in den Automaten hinzu, sofern es nicht abgelaufen ist.")

                        barcode_add = st.text_input(
                            "📌 Barcode der Ware eingeben", 
                            key="barcode_add_automat",
                            help="Scannen oder geben Sie den Barcode des Medikaments ein."
                        )

                        if st.button("📥 In Automaten verschieben", key="btn_add_automat", use_container_width=True):
                            if barcode_add:
                                message = automat.ware_zum_automaten_hinzufuegen(barcode_add)

                                if "Fehler" in message:
                                    st.toast(f" {message}", icon="🚫")
                                    datenbank.log_aktion(f"🚫 Fehler beim Verschieben in den Automaten - {message}")
                                else:
                                    st.toast(f"✅ Medikament erfolgreich verschoben!", icon="✅")
                                    datenbank.log_aktion(f"✅ Medikament {barcode_add} erfolgreich in den Automaten verschoben.")

                                time.sleep(0.75)  # ⏳ Verzögerung für eine sanfte Aktualisierung
                                st.rerun()

                # 🗑 Expander für "Ware aus Automaten entfernen"
                with col2:
                    with st.expander("🗑 Ware aus Automaten entfernen", expanded=True):
                        st.write("Entfernen Sie ein Medikament aus dem Automaten und legen Sie es zurück ins Lager.")

                        barcode_remove = st.text_input(
                            "📌 Barcode der Ware eingeben", 
                            key="barcode_remove_automat",
                            help="Scannen oder geben Sie den Barcode des Medikaments ein."
                        )

                        if st.button("🗑 Medikament entfernen", key="btn_remove_automat", use_container_width=True):
                            if barcode_remove:
                                message = automat.ware_aus_automaten_entfernen(barcode_remove)

                                if "Fehler" in message:
                                    st.toast(f"{message}", icon="🚫")
                                    datenbank.log_aktion(f"🚫 Fehler beim Entfernen aus dem Automaten - {message}")
                                else:
                                    st.toast(f"✅ Medikament erfolgreich entfernt!", icon="✅")
                                    datenbank.log_aktion(f"✅ Medikament {barcode_remove} erfolgreich aus dem Automaten entfernt.")

                                time.sleep(0.75)  # ⏳ Verzögerung für UI-Aktualisierung
                                st.rerun()


            # 🛒 TAB 3: Bestellungen & Warenkorb
            with tab3:
                st.subheader("🛒 Bestellungen & Warenkorb")

                # 📦 Expander für Barcode-Scan & Warenkorb-Hinzufügen
                with st.expander("🔍 Medikament zum Warenkorb hinzufügen", expanded=True):
                    st.write("Scannen oder geben Sie den Barcode eines Medikaments ein, um es dem Warenkorb hinzuzufügen.")

                    barcode_bestellung = st.text_input(
                        "📌 Barcode scannen",
                        key="warenkorb_barcode",
                        help="Scannen oder geben Sie den Barcode des Medikaments ein."
                    )

                    if st.button("➕ Medikament hinzufügen", key="btn_add_warenkorb", use_container_width=True):
                        if barcode_bestellung:
                            message = automat.ware_zum_warenkorb_hinzufuegen(barcode_bestellung)

                            if "Fehler" in message:
                                st.toast(f"{message}", icon="🚫")
                                datenbank.log_aktion(f"🚫 Fehler beim Hinzufügen zum Warenkorb - {message}")
                            else:
                                st.toast(f"✅ Medikament hinzugefügt!", icon="✅")
                                datenbank.log_aktion(f"✅ Medikament {barcode_bestellung} zum Warenkorb hinzugefügt.")

                            time.sleep(0.75)
                            st.rerun()

                # 📦 Expander für Warenkorb-Anzeige
                with st.expander("🛒 Warenkorb anzeigen", expanded=True):
                    if st.session_state.warenkorb:
                        warenkorb_df = pd.DataFrame(st.session_state.warenkorb)
                        
                        # ✅ Erster Buchstabe der Spaltennamen groß schreiben
                        warenkorb_df.columns = warenkorb_df.columns.str.capitalize()

                        st.dataframe(warenkorb_df, use_container_width=True)


                        # 🔄 Button-Layout für Warenkorb-Aktionen
                        col1, col2 = st.columns([1, 1])

                        with col1:
                            if st.button("📦 Bestellung abschicken", key="btn_checkout", use_container_width=True):
                                message = automat.bestellung_abschicken(st.session_state.kundennummer)

                                if "erfolgreich aufgegeben" in message:
                                    bestellgruppe_id = message.split(" ")[1]  # Extrahiere Bestell-ID
                                    medikamenten_namen = message.split(":")[-1]  # Extrahiere Medikamentennamen
                                    st.toast(f"✅ Bestellung {bestellgruppe_id} erfolgreich!", icon="✅")
                                    datenbank.log_aktion(f"✅ Bestellung {bestellgruppe_id} aufgegeben mit {medikamenten_namen}")
                                else:
                                    st.toast(f" {message}", icon="🚫")
                                    datenbank.log_aktion(f"🚫 Fehler bei Bestellung - {message}")

                                time.sleep(0.75)
                                st.rerun()

                        with col2:
                            if st.button("🗑 Warenkorb leeren", key="btn_clear_cart", use_container_width=True):
                                st.session_state.warenkorb = []
                                st.toast("🗑 Warenkorb wurde erfolgreich geleert!", icon="✅")
                                datenbank.log_aktion("🗑 Benutzer hat den Warenkorb geleert")
                                time.sleep(0.75)
                                st.rerun()

                    else:
                        st.info("🛒 Ihr Warenkorb ist leer.")

                # 📋 Expander für Bestellübersicht
                with st.expander("📋 Meine Bestellungen anzeigen", expanded=True):
                    bestellungen_df = automat.get_bestellungen_gruppiert(st.session_state.kundennummer)

                    if not bestellungen_df.empty:
                        st.dataframe(bestellungen_df, use_container_width=True)

                        # 🔍 Filter nur offene Bestellungen für Stornierung
                        offene_bestellungen = bestellungen_df[bestellungen_df["Status"] == "Offen"]

                        if not offene_bestellungen.empty:
                            bestell_options = {
                                f"Bestellung {row['Bestell-ID']}: {row['Medikamente']}": row['Bestell-ID']
                                for _, row in offene_bestellungen.iterrows()
                            }

                            selected_bestell_text = st.selectbox(
                                "📌 Bestellung zum Stornieren auswählen",
                                list(bestell_options.keys()),
                                key="bestell_storno"
                            )

                            if st.button("🗑 Bestellung stornieren", key="btn_storno", use_container_width=True):
                                bestell_id = bestell_options[selected_bestell_text]
                                message = automat.bestellung_stornieren(bestell_id, st.session_state.kundennummer)

                                if "Fehler" in message:
                                    st.toast(f"{message}", icon="🚫")
                                    datenbank.log_aktion(f"🚫 Fehler bei der Stornierung von Bestellung {bestell_id}: {message}")
                                else:
                                    st.toast(f"✅ Bestellung {bestell_id} storniert!", icon="✅")
                                    datenbank.log_aktion(f"✅ Bestellung {bestell_id} erfolgreich storniert!")

                                time.sleep(1)
                                st.rerun()
                        else:
                            st.info("🚫 Keine offenen Bestellungen vorhanden.")
                            datenbank.log_aktion("📋 Benutzer hat Bestellübersicht aufgerufen - Keine offenen Bestellungen gefunden.")
                    else:
                        st.info("🚫 Keine Bestellungen vorhanden.")
                        datenbank.log_aktion("📋 Benutzer hat Bestellübersicht aufgerufen - Keine Bestellungen gefunden.")



        elif menu[choice] == "⚠️ Warnungen verwalten":

            
                st.subheader("📋 Abgelaufene Medikamente")


                # 🔍 Expander für die Filteroptionen
                with st.expander("🔍 Warnungen filtern", expanded=True):
                    st.write("Filtern Sie die Warnungen nach Lager oder Automat.")

                    ort_filter_warnungen = st.selectbox(
                        "📌 Ort auswählen", 
                        ["Alle", "Lager", "Automat"], 
                        index=0, 
                        key="warnungen_filter", 
                        help="Filtern Sie nach Lager oder Automat."
                    )

                # 📋 Lade die abgelaufenen Medikamente basierend auf dem Filter
                warnungen = warnung.get_warnungen(ort_filter=ort_filter_warnungen if ort_filter_warnungen != "Alle" else None)

                # ✅ Falls keine abgelaufenen Medikamente vorhanden sind
                if warnungen.empty:
                    st.success("✅ Keine abgelaufenen Medikamente!")
                    st.toast("✅ Keine abgelaufenen Medikamente im System.", icon="✅")
                    datenbank.log_aktion("✅ Keine abgelaufenen Medikamente gefunden.")
                else:
                    st.warning(f"⚠️ Es gibt {len(warnungen)} abgelaufene Medikamente!")
                    st.toast(f"⚠️ Achtung: {len(warnungen)} abgelaufene Medikamente gefunden!", icon="⚠️")
                    datenbank.log_aktion(f"⚠️ Benutzer hat {len(warnungen)} abgelaufene Medikamente aufgerufen.")

                    # 📊 Zeige die Tabelle mit abgelaufenen Medikamenten
                    st.dataframe(warnungen, use_container_width=True, height=300)


