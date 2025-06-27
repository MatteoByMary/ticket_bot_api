# Support Ticket AI Assistant

API FastAPI pour l'analyse automatique et le suivi des tickets de support client.

##  Fonctionnalités

- **Analyse automatique** : Génère des tickets structurés à partir de messages clients
- **Questions de suivi** : Propose des questions intelligentes pour compléter les informations
- **Multi-backends** : Support Ollama et Mistral
- **API REST** : Endpoints simples et documentés
- **Docker Ready** : Déploiement containerisé

##  Structure du projet

```
.
├── main.py                    # Point d'entrée FastAPI
├── models/
│   ├── __init__.py
│   └── schemas.py            # Modèles Pydantic
├── services/
│   ├── __init__.py
│   ├── model_service.py      # Service IA
│   └── prompt_service.py     # Gestion des prompts
├── requirements.txt          # Dépendances Python
├── Dockerfile               # Configuration Docker
├── docker-compose.yml       # Orchestration complète
└── README.md               # Ce fichier
```

##  Installation

### Option 1: Installation locale

```bash
# Cloner le projet
git clone <votre-repo>
cd support-ticket-ai

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement
cp .env.example .env
# Éditer .env selon vos besoins

# Lancer l'API
uvicorn main:app --reload
```

### Option 2: Docker Compose (Recommandé)

```bash
# Lancer tout le stack (API + Ollama)
docker-compose up -d

# Voir les logs
docker-compose logs -f

# Arrêter
docker-compose down
```

##  Configuration

Variables d'environnement importantes :

| Variable | Défaut | Description |
|----------|--------|-------------|
| `MODEL_BACKEND` | `ollama` | Backend IA (`ollama` ou `mistral`) |
| `OLLAMA_URL` | `http://localhost:11434/api/generate` | URL du service Ollama |
| `OLLAMA_MODEL_NAME` | `mistral:instruct` | Modèle Ollama à utiliser |
| `CORS_ORIGINS` | `http://localhost:5173` | Origines CORS autorisées |

##  API Endpoints

### `POST /analyze`
Analyse un message client et génère un ticket structuré.

**Body:**
```json
{
  "message": "Mon imprimante ne marche plus depuis ce matin",
  "history": ["Bonjour", "J'ai un problème"]
}
```

**Response:**
```json
{
  "success": true,
  "data": "JSON du ticket généré",
  "message": "Ticket analysé avec succès"
}
```

### `POST /followup`
Génère une question de suivi pour compléter un ticket.

**Body:**
```json
{
  "ticket": {
    "titre": "Problème imprimante",
    "categorie": "[INCONNU]",
    "description": "Imprimante en panne"
  },
  "history": ["Bonjour"]
}
```

### `GET /health`
Vérification de l'état du service.

##  Tests

```bash
# Test de l'API
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{"message": "Test message"}'

# Health check
curl http://localhost:8000/health
```

##  Docker

### Build manuel
```bash
docker build -t support-ticket-ai .
docker run -p 8000:8000 support-ticket-ai
```

### Avec Ollama
```bash
# Démarrer Ollama
docker run -d -p 11434:11434 --name ollama ollama/ollama

# Installer un modèle
docker exec ollama ollama pull mistral:instruct

# Démarrer l'API
docker run -p 8000:8000 --link ollama support-ticket-ai
```

##  Monitoring

- **Logs** : Les logs sont centralisés avec le module `logging`
- **Health Check** : Endpoint `/health` pour les probes
- **Métriques** : Codes de retour HTTP standardisés

##  Gestion d'erreurs

L'API gère :
-  Timeouts des services IA
-  Erreurs de connexion
-  Validation des données
-  Messages d'erreur explicites

##  Sécurité

- **CORS** : Configuration sécurisée
- **Validation** : Tous les inputs sont validés
- **Timeouts** : Protection contre les appels longs
- **Logs** : Audit trail complet

##  Performance

- **Timeout** : 30s max pour les appels IA
- **Async** : Toutes les opérations sont asynchrones
- **Cache** : Prêt pour l'ajout de cache Redis

##  Contribution

1. Fork le projet
2. Crée une branche (`git checkout -b feature/amazing-feature`)
3. Commit tes changes (`git commit -m 'Add amazing feature'`)
4. Push (`git push origin feature/amazing-feature`)
5. Ouvre une Pull Request

## 📄 License

Ce projet est sous `LICENSE`.

##  Support

- **Documentation API** : http://localhost:8000/docs (Swagger)