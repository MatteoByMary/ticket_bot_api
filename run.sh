
# Script de démarrage pour le projet Support Ticket AI

echo "🚀 Démarrage du Support Ticket AI Assistant"

# Vérification de Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker n'est pas installé. Veuillez l'installer d'abord."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose n'est pas installé. Veuillez l'installer d'abord."
    exit 1
fi

# Création du fichier .env s'il n'existe pas
if [ ! -f .env ]; then
    echo "📝 Création du fichier .env..."
    cp .env.example .env
    echo "✅ Fichier .env créé. Vous pouvez le modifier si nécessaire."
fi

# Démarrage des services
echo "🐳 Démarrage des conteneurs Docker..."
docker-compose up -d

# Attendre que les services soient prêts
echo "⏳ Attente du démarrage des services..."
sleep 10

# Vérification de l'API
echo "🔍 Vérification de l'API..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ API prête sur http://localhost:8000"
    echo "📚 Documentation disponible sur http://localhost:8000/docs"
else
    echo "❌ L'API ne répond pas. Vérifiez les logs avec: docker-compose logs"
fi

# Vérification d'Ollama
echo "🔍 Vérification d'Ollama..."
if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "✅ Ollama prêt sur http://localhost:11434"
    
    # Vérifier si le modèle est installé
    if docker exec $(docker-compose ps -q ollama) ollama list | grep -q mistral; then
        echo "✅ Modèle Mistral déjà installé"
    else
        echo "📥 Installation du modèle Mistral..."
        docker exec $(docker-compose ps -q ollama) ollama pull mistral:instruct
        echo "✅ Modèle Mistral installé"
    fi
else
    echo "❌ Ollama ne répond pas. Vérifiez les logs avec: docker-compose logs ollama"
fi

echo ""
echo "🎉 Démarrage terminé !"
echo ""
echo "📋 Commandes utiles :"
echo "  - Voir les logs: docker-compose logs -f"
echo "  - Arrêter: docker-compose down"
echo "  - Redémarrer: docker-compose restart"
echo "  - Tester l'API: curl http://localhost:8000/health"
echo ""
echo "🌐 URLs importantes :"
echo "  - API: http://localhost:8000"
echo "  - Documentation: http://localhost:8000/docs"
echo "  - Ollama: http://localhost:11434"