FROM python:3.11-slim

WORKDIR /app

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copie des requirements
COPY requirements.txt .

# Installation des dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copie du code source
COPY . .

# Création des dossiers manquants
RUN mkdir -p models services

# Exposition du port
EXPOSE 8000

# Variables d'environnement par défaut
ENV MODEL_BACKEND=ollama
ENV OLLAMA_URL=http://localhost:11434/api/generate
ENV CORS_ORIGINS=http://localhost:5173

# Commande de démarrage
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]