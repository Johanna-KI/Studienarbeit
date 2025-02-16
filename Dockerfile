# Basis-Image mit Python 3.10
FROM python:3.10

# Setze das Arbeitsverzeichnis im Container
WORKDIR /app

# Installiere System-Abhängigkeiten (einschließlich SQLite-Paket)
RUN apt-get update && apt-get install -y sqlite3 && rm -rf /var/lib/apt/lists/*

# Kopiere die Abhängigkeitsdateien in den Container
COPY requirements.txt ./

# Installiere die Abhängigkeiten
RUN pip install --upgrade pip && pip install -r requirements.txt

# Kopiere den Rest des Codes
COPY . .

# Setze das Startkommando für die Streamlit-App
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
