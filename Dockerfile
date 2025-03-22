# Offizielles Python-Image als Basis nutzen
FROM python:3.9

# Arbeitsverzeichnis setzen
WORKDIR /app

# Alle Dateien in den Container kopieren
COPY . /app

# Sicherstellen, dass 'pip' und 'setuptools' aktuell sind
RUN pip install --no-cache-dir --upgrade pip setuptools

# Abhängigkeiten aus pyproject.toml installieren
RUN pip install --no-cache-dir .

# Port für Streamlit freigeben
EXPOSE 8501

# Setze das Startkommando für die Streamlit-App
CMD ["streamlit", "run", "src/lagersystem/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
