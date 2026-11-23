
# Image de MaintAI : code et bibliothèques

# 1. Image Python
FROM python:3.11-slim

# 2. Répertoire de travail
WORKDIR /app

# 3. Installer les dépendances
COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

# 4. Copier le code
COPY maintai/ ./maintai/
COPY ui/ ./ui/

# 5. Variables d'environnement
ENV MAINTAI_MODELS_DIR=/app/models
ENV MAINTAI_DATA_PATH=/app/data/sensors.csv

# 6. Exposer le port et démarrer l'API
EXPOSE 8000

CMD ["uvicorn", "maintai.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
