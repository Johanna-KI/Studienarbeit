# Basis-Image mit Python 3.10
FROM python:3.10

# Setze das Arbeitsverzeichnis im Container
WORKDIR /app

# Installiere System-Abhängigkeiten (einschließlich SQLite)
RUN apt-get update && apt-get install -y sqlite3 && rm -rf /var/lib/apt/lists/*

# Kopiere requirements.txt und installiere Python-Abhängigkeiten
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Kopiere den gesamten Code in den Container
COPY ./src/lagersystem ./src/lagersystem

# Setze PYTHONPATH, damit src/lagersystem importierbar ist
ENV PYTHONPATH="/app/src"

# Setze das Startkommando für die Streamlit-App
CMD ["streamlit", "run", "src/lagersystem/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
