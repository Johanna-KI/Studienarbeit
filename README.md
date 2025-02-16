# **Lagersystem für Medikamente**

Dieses Projekt ist eine Streamlit-Anwendung, die ein Lagersystem für Medikamente simuliert. Die Anwendung ermöglicht es, Medikamente im Lagerbestand und Automatenbestand zu verwalten, einschließlich Hinzufügen, Löschen, Aktualisieren von Mengen sowie Befüllen eines Automaten.

---

## **Funktionen**

- **Hinzufügen von Waren**: Neue Medikamente in den Lagerbestand aufnehmen.
- **Mengen aktualisieren**: Die Menge eines Medikaments im Lagerbestand ändern.
- **Automaten befüllen**: Medikamente aus dem Lagerbestand in den Automatenbestand verschieben.
- **Bestellungen**: Medikamente aus dem Automatenbestand entnehmen.
- **Löschen von Waren**: Medikamente aus dem Lager- oder Automatenbestand entfernen.
- **Anzeige des Bestands**: Übersicht über den Lager- und Automatenbestand.

---

## **Voraussetzungen**

### **Option 1: Docker verwenden**
- Docker muss auf Ihrem System installiert sein. [Docker installieren](https://docs.docker.com/get-docker/)

### **Option 2: Python verwenden**
- Python 3.9 oder neuer und Pip sollten installiert sein.


---

## **Schritt-für-Schritt-Anleitung**

### **1. Projekt klonen**
Klonen Sie das Repository auf Ihren Computer:
```bash
git clone https://github.com/Johanna-KI/lagersystem.git
cd lagersystem
```

### **2. Ausführung der Anwendung**

#### **Option 1: Docker verwenden**

##### **Schritt 2.1: Docker installieren**
Falls Docker noch nicht installiert ist, folgen Sie der Anleitung auf der offiziellen Docker-Website: [Docker installieren](https://docs.docker.com/get-docker/).

##### **Schritt 2.2: Docker-Image erstellen und Container starten**
Erstellen Sie das Docker-Image, indem Sie im Projektverzeichnis den folgenden Befehl ausführen: 
(WICHTIG: Die Docker Desktop App muss währenddessen laufen)
```bash
docker-compose up --build
```

##### **Schritt 2.3: Anwendung im Browser öffnen**
Öffnen Sie Ihren Browser und navigieren Sie zu:
[WebApp](http://localhost:8501)

--


#### **Option 2: Python verwenden**

##### **Schritt 2.1: Python installieren**
Falls Python noch nicht installiert ist, laden Sie Python 3.9 oder neuer von der offiziellen Website herunter und installieren Sie es:
[Python installieren](https://www.python.org/downloads/)

##### **Schritt 2.2: Virtuelle Umgebung erstellen (optional)**
Erstellen Sie eine virtuelle Umgebung und aktivieren Sie sie:
```bash
# Virtuelle Umgebung erstellen
python -m venv venv

# Virtuelle Umgebung aktivieren
# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

##### **Schritt 2.3: Requirements installieren**
Installieren Sie die benötigten Python-Pakete mit pip:
```bash
pip install -r requirements.txt
```

##### **Schritt 2.4: Anwendung starten**
Starten Sie die Streamlit-Anwendung:
```bash
streamlit run main.py
```

##### **Schritt 2.5: Anwendung im Browser öffnen**
Nach dem Starten der Anwendung öffnet sich ein neuer Browser-Tab oder Sie können die Anwendung über den folgenden Link aufrufen:
[WebApp](http://localhost:8501)



