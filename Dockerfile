# Basis-Image mit Python
FROM python:3.11.9

# Arbeitsverzeichnis im Container erstellen und festlegen
WORKDIR /studienarbeit

# Kopieren der Abhängigkeitsdatei und Installation der Abhängigkeiten
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Kopieren der App und der Datenbankdatei
COPY main.py main.py
COPY lagerbestand.db lagerbestand.db

# Umgebungsvariablen für Streamlit konfigurieren
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_ENABLECORS=false

# Exponieren des Streamlit-Ports
EXPOSE 8501

# Starten der App
CMD ["streamlit", "run", "main.py"]
