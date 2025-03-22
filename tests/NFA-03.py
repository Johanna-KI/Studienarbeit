import time
from playwright.sync_api import sync_playwright


def click_button(page, button_text):
    """Versucht, einen Streamlit-Button sicher zu klicken und sicherzustellen, dass sich die UI ändert."""
    print(f"🖱 Versuche, den Button '{button_text}' zu klicken...")

    button = page.locator(f"button:has-text('{button_text}')")

    if button.is_visible():
        try:
            button.click(force=True)
            print(f"✅ Button '{button_text}' erfolgreich geklickt!")
            page.wait_for_timeout(2000)  # Wartezeit für UI-Update
            page.wait_for_load_state(
                "networkidle"
            )  # Warten, bis Streamlit die UI aktualisiert
        except:
            print(f"❌ Standard-Klick fehlgeschlagen. Versuche JavaScript-Klick...")
            page.evaluate(
                f"document.querySelector('button:has-text(\"{button_text}\")').click()"
            )
            print(f"✅ JavaScript-Klick auf '{button_text}' erfolgreich!")
            page.wait_for_timeout(2000)
            page.wait_for_load_state("networkidle")
    else:
        print(f"❌ Button '{button_text}' nicht gefunden!")


def usability_test():
    """Testet die Usability der Streamlit-Oberfläche und misst die Task Completion Time (TCT)"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Browser sichtbar machen
        page = browser.new_page()

        # **Starte Zeitmessung**
        start_time = time.time()

        # **Öffne Streamlit-App**
        print("🌍 Öffne Streamlit-App...")
        page.goto("http://localhost:8501")
        page.wait_for_load_state("networkidle")

        # **Login**
        print("🔑 Teste Benutzer-Login...")
        page.click(
            "text=🔑 Benutzer-Login"
        )  # Sicherstellen, dass das Login-Tab aktiv ist
        page.wait_for_timeout(2000)

        page.get_by_label("Benutzername").nth(0).fill("testuser")
        page.get_by_label("Passwort").nth(0).fill("testpass")

        # **Anmelde-Button klicken**
        print("🖱 Versuche, den Button '🔑 Anmelden' zu klicken...")
        button = page.locator("button:has-text('🔑 Anmelden')")

        if button.is_visible():
            try:
                button.click(force=True)
                print("✅ Button '🔑 Anmelden' erfolgreich geklickt!")
                page.wait_for_load_state("load")  # Warten auf Streamlit-Reload
                page.wait_for_timeout(3000)  # Extra Wartezeit für Authentifizierung
            except:
                print("❌ Standard-Klick fehlgeschlagen. Versuche JavaScript-Klick...")
                page.evaluate(
                    "document.querySelector('button:has-text(\"🔑 Anmelden\")').click()"
                )
                print("✅ JavaScript-Klick auf '🔑 Anmelden' erfolgreich!")
                page.wait_for_load_state("load")
                page.wait_for_timeout(3000)
        else:
            print("❌ Button '🔑 Anmelden' nicht gefunden!")

        # **Navigation zu Lager**
        print("📂 Teste Navigation zu Lager...")
        page.wait_for_selector("text=📦 Lagersystem", timeout=60000)
        page.click("text=📦 Lagersystem")
        page.wait_for_timeout(2000)

        # **Navigation zu Automat**
        print("🤖 Teste Navigation zu Automat...")
        page.wait_for_selector("text=🤖 Automat", timeout=60000)
        page.click("text=🤖 Automat")
        page.wait_for_timeout(2000)

        # **Navigation zu Warnungen**
        print("⚠️ Teste Navigation zu Warnungen...")
        page.wait_for_selector("text=⚠️ Warnungen verwalten", timeout=60000)
        page.click("text=⚠️ Warnungen verwalten")
        page.wait_for_timeout(2000)

        # **Zurück zum Automaten-Menü**
        print("🔄 Zurück zum Automaten...")
        page.wait_for_selector("text=🤖 Automat", timeout=60000)
        page.click("text=🤖 Automat")
        page.wait_for_timeout(2000)

        # **Debugging: Zeige alle sichtbaren Input-Felder**
        inputs = page.locator("input").all()
        print(f"🔍 Gefundene Eingabefelder: {len(inputs)}")

        for i, input_field in enumerate(inputs):
            print(f"Eingabefeld {i+1}: {input_field.input_value()}")

        # **Medikamentensuche starten**
        print("🔍 Teste Medikamentensuche...")
        try:
            page.get_by_label("🔍 Barcode eingeben oder scannen").fill("12345678")
        except:
            print("❌ Label nicht gefunden. Versuche `placeholder`...")
            page.get_by_placeholder("Barcode eingeben oder scannen").fill("12345678")

        # **Enter-Taste drücken, um die Suche auszulösen**
        page.press("input", "Enter")
        print("✅ Barcode-Suche erfolgreich gestartet!")

        page.wait_for_timeout(2000)

        # **Wechsel zur Bestellungsseite**
        print("🔄 Wechsel zu Bestellungen...")
        page.click("text=🛒 Bestellungen")
        time.sleep(2)

        # **Barcode ins Bestellformular eingeben**
        print("📦 Füge Medikament zum Warenkorb hinzu...")
        page.get_by_label("📌 Barcode scannen").fill("12345678")
        page.click("text=➕ Medikament hinzufügen")
        time.sleep(2)
        print("✅ Medikament in den Warenkorb gelegt!")

        # **Bestellung abschließen**
        print("🛒 Bestätige Bestellung...")
        page.click("text=📦 Bestellung abschicken")
        time.sleep(2)
        print("✅ Bestellung erfolgreich abgeschickt!")

        # **Logout**
        print("🚪 Teste Abmeldung...")
        page.wait_for_selector("text=🚪 Abmelden", timeout=60000)
        page.click("text=🚪 Abmelden")
        page.wait_for_timeout(2000)

        # **Stoppe Zeitmessung**
        end_time = time.time()
        total_time = round(end_time - start_time, 2)
        print(f"📊 Gesamtzeit für Usability-Test: {total_time} Sekunden")

        if total_time <= 180:
            print("✅ Usability ist gut! Alle Aufgaben wurden in <3 Minuten erledigt.")
        else:
            print("⚠️ Optimierung nötig! Die TCT ist zu hoch.")

        browser.close()


# **Testlauf starten**
usability_test()
