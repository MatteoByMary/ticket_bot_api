# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
import logging
import json
from enum import Enum

# Import des services
from services.model_service import ModelService
from services.prompt_service import PromptService
from services.localisation_service import LocationService
from models.schemas import TicketInput, FollowUpInput, ApiResponse, HistoryMessage

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from dotenv import load_dotenv
load_dotenv()

# Configuration
class Config:
    MODEL_BACKEND = os.getenv("MODEL_BACKEND", "mistral")
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
    OLLAMA_MODEL_NAME = os.getenv("OLLAMA_MODEL_NAME", "mistral:instruct")
    
    @classmethod
    def validate(cls):
        """Valide la configuration"""
        if cls.MODEL_BACKEND not in ["mistral", "ollama"]:
            raise ValueError(f"Backend non supporté: {cls.MODEL_BACKEND}")
        
        if cls.MODEL_BACKEND == "mistral" and not os.getenv("MISTRAL_API_KEY"):
            logger.warning("MISTRAL_API_KEY non configurée pour le backend Mistral")

# Validation des backends supportés
class ModelBackend(str, Enum):
    MISTRAL = "mistral"
    OLLAMA = "ollama"

# Initialisation de l'app
app = FastAPI(
    title="Support Ticket AI Assistant",
    description="API pour l'analyse et le suivi des tickets de support",
    version="1.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Initialisation des services
prompt_service = PromptService()
model_service = None
localisation_service = None

@app.on_event("startup")
async def startup_event():
    """Vérifications et initialisation au démarrage"""
    global model_service, localisation_service
    
    try:
        # Validation de la configuration
        Config.validate()
        
        # Initialisation du service de modèle
        model_service = ModelService(
            Config.MODEL_BACKEND, 
            Config.OLLAMA_URL, 
            Config.OLLAMA_MODEL_NAME,
            prompt_service
        )

        localisation_service = LocationService()
        
        logger.info(f"Application démarrée avec le backend: {Config.MODEL_BACKEND}")
        
        # Test de chargement des prompts
        try:
            prompt_service.get_system_prompt()
            prompt_service.get_followup_system_prompt()
            prompt_service.get_minimal_system_prompt()
            logger.info("Tous les prompts ont été chargés avec succès")
        except Exception as e:
            logger.error(f"Erreur lors du chargement des prompts: {str(e)}")
            raise
            
    except Exception as e:
        logger.error(f"Erreur lors du démarrage: {str(e)}")
        raise

@app.get("/health")
async def health_check():
    """Endpoint de santé détaillé"""
    try:
        status = {
            "status": "healthy",
            "backend": Config.MODEL_BACKEND,
            "model_service": model_service.get_status() if model_service else None,
            "prompts": {
                "base_prompt": bool(prompt_service._cache.get("base_prompt") or True),
                "followup_prompt": bool(prompt_service._cache.get("followup_prompt") or True),
                "minimal_prompt": bool(prompt_service._cache.get("minimal_prompt") or True)
            }
        }
        return status
    except Exception as e:
        logger.error(f"Erreur dans health check: {str(e)}")
        return {"status": "unhealthy", "error": str(e)}

@app.post("/analyze", response_model=ApiResponse)
async def analyze_ticket(ticket: TicketInput) -> ApiResponse:
    """
    Analyse un message de support et génère un ticket structuré
    """
    if not model_service or not localisation_service:
        raise HTTPException(status_code=500, detail="Service non initialisé")
    
    try:
        logger.info(f"Analyse du ticket: {ticket.message[:50]}...")
        
        # Le ticket.history est maintenant une liste d'objets HistoryMessage
        result_str = await model_service.analyze_ticket(ticket.message, ticket.history)

        logger.info(f"Réponse du modèle: {result_str}...")

        parsed_result = {}
        try:
            if result_str:
                parsed_result = json.loads(result_str)
            else:
                raise json.JSONDecodeError("La réponse du modèle est vide", "", 0)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON invalide reçu du modèle: {str(e)}")
            # MODIFIÉ : Retourner une instance de ApiResponse en cas d'erreur
            return ApiResponse(
                success=False,
                data=result_str,
                message="Le modèle a retourné une réponse invalide ou vide.",
                error=str(e)
            )

        if 'localisation' in parsed_result and parsed_result['localisation']:
            user_location = parsed_result['localisation']
            normalized_location = localisation_service.find_best_match(user_location)
            if normalized_location:
                parsed_result['localisation'] = normalized_location

        # MODIFIÉ : Retourner une instance de ApiResponse en cas de succès
        return ApiResponse(
            success=True,
            data=parsed_result,
            message="Ticket analysé avec succès"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# MODIFIÉ : Le response_model est maintenant ApiResponse
@app.post("/followup", response_model=ApiResponse)
async def generate_followup(data: FollowUpInput) -> ApiResponse:
    """
    Génère une question de suivi basée sur un ticket partiellement rempli
    """
    logger.info("Génération d'une question de suiviiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii")
    if not model_service:
        raise HTTPException(status_code=500, detail="Service non initialisé")
    
    try:
        logger.info("Génération d'une question de suivi")
        
        if not data.ticket:
            raise HTTPException(status_code=400, detail="Le ticket ne peut pas être vide")
        
        prompt = prompt_service.build_followup_prompt(data.ticket, data.history)
        # Note: data.history est maintenant une liste d'objets
        result = await model_service.generate_followup(prompt, data.history)
        
        logger.info(f"Réponse du modèle: {result}...")

        # MODIFIÉ : Retourner une instance de ApiResponse
        return ApiResponse(
            success=True,
            data={"question": result},
            message="Question de suivi générée avec succès"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la génération: {str(e)}")
        # MODIFIÉ : Retourner une instance de ApiResponse en cas d'erreur
        return ApiResponse(
            success=False,
            message="Erreur interne lors de la génération de la question.",
            error=str(e)
        )

@app.post("/admin/reload-prompts")
async def reload_prompts():
    """Endpoint pour recharger les prompts (utile en développement)"""
    try:
        prompt_service.invalidate_cache()
        # Test de rechargement
        prompt_service.get_system_prompt()
        prompt_service.get_followup_system_prompt()
        prompt_service.get_minimal_system_prompt()
        
        return {
            "success": True,
            "message": "Prompts rechargés avec succès"
        }
    except Exception as e:
        logger.error(f"Erreur lors du rechargement des prompts: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du rechargement: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)