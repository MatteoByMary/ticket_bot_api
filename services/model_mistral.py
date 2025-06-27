# services/model_mistral.py
import os
import json
import httpx
import asyncio
from fastapi import HTTPException
import logging
from typing import Optional, List

# --- MODIFIÉ : Import du modèle de message d'historique ---
# Ce chemin d'import suppose que vos dossiers 'models' et 'services' sont au même niveau.
from models.schemas import HistoryMessage

logger = logging.getLogger(__name__)

MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MODEL_NAME = os.getenv("MISTRAL_MODEL_NAME", "mistral-large-latest")

# Configuration retry
MAX_RETRIES = 3
RETRY_DELAY = 2  # secondes
BACKOFF_MULTIPLIER = 2

# Modèles disponibles par ordre de préférence
MISTRAL_MODELS = [
    "mistral-small-latest",
    "mistral-medium-latest", 
    "mistral-large-latest"
]

class MistralService:
    def __init__(self, prompt_service):
        self.prompt_service = prompt_service
        
        if not MISTRAL_API_KEY:
            logger.warning("Clé API Mistral non configurée")
    
    # --- MODIFIÉ : La signature de la méthode utilise maintenant List[HistoryMessage] ---
    async def analyze_ticket(self, message: str, history: List[HistoryMessage] = None, retry_count: int = 0):
        """Appel à l'API Mistral pour l'analyse de tickets avec gestion de l'historique structuré."""
        logger.info(f"Appel Mistral API (tentative {retry_count + 1}/{MAX_RETRIES + 1})")
        
        if not MISTRAL_API_KEY:
            raise HTTPException(status_code=500, detail="Clé API Mistral manquante (MISTRAL_API_KEY)")

        current_model = self._get_model_for_retry(retry_count)
        logger.info(f"Utilisation du modèle: {current_model}")

        system_prompt = (self.prompt_service.get_system_prompt() 
                        if retry_count <= 1
                        else self.prompt_service.get_minimal_system_prompt())

        messages = [{"role": "system", "content": system_prompt}]
        
        # --- MODIFIÉ : Logique de traitement de l'historique structuré ---
        if history:
            for hist_msg in history:
                messages.append({"role": hist_msg.role, "content": hist_msg.content})
        
        messages.append({"role": "user", "content": message})

        headers = {
            "Authorization": f"Bearer {MISTRAL_API_KEY}",
            "Content-Type": "application/json"
        }

        temperature = 0.3 + (retry_count * 0.1)
        max_tokens = 800 if retry_count == 0 else 600

        payload = {
            "model": current_model,
            "messages": messages,
            "temperature": min(temperature, 0.7),
            "top_p": 0.95,
            "max_tokens": max_tokens
        }

        # La logique de try/except reste la même...
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                logger.debug(f"Envoi requête avec modèle {current_model}")
                response = await client.post(MISTRAL_API_URL, headers=headers, json=payload)
                
                if response.status_code == 429:
                    # ... gestion des retries ...
                    if retry_count < MAX_RETRIES:
                        delay = RETRY_DELAY * (BACKOFF_MULTIPLIER ** retry_count)
                        logger.info(f"Attente de {delay}s avant retry...")
                        await asyncio.sleep(delay)
                        return await self.analyze_ticket(message, history, retry_count + 1)
                    else:
                        if current_model != "mistral-small-latest":
                            logger.info("Tentative finale avec mistral-small-latest")
                            return await self._try_with_minimal_model(message, history)
                        else:
                            raise HTTPException(status_code=429, detail="Limite de capacité Mistral atteinte.")
                
                elif response.status_code != 200:
                    error_detail = response.text
                    logger.error(f"Erreur API Mistral {response.status_code}: {error_detail}")
                    raise HTTPException(status_code=502, detail=f"Erreur API Mistral ({response.status_code}): {error_detail}")
                
                response_data = response.json()
                if "choices" not in response_data or not response_data["choices"]:
                    raise HTTPException(status_code=502, detail="Réponse invalide de l'API Mistral")
                
                content = response_data["choices"][0]["message"]["content"]
                logger.info(f"Réponse Mistral reçue avec succès (modèle: {current_model})")
                return content.strip()
                
        except httpx.TimeoutException:
            logger.error("Timeout lors de l'appel à Mistral API")
            if retry_count < MAX_RETRIES:
                await asyncio.sleep(RETRY_DELAY)
                return await self.analyze_ticket(message, history, retry_count + 1)
            raise HTTPException(status_code=504, detail="Timeout de l'API Mistral")
        # ... reste de la gestion d'erreurs ...
        except Exception as e:
            logger.error(f"Erreur inattendue lors de l'appel Mistral: {str(e)}")
            if retry_count < MAX_RETRIES:
                await asyncio.sleep(RETRY_DELAY)
                return await self.analyze_ticket(message, history, retry_count + 1)
            raise HTTPException(status_code=502, detail=f"Erreur Mistral: {str(e)}")

    # --- MODIFIÉ : La signature de la méthode utilise maintenant List[HistoryMessage] ---
    async def generate_followup(self, prompt: str, history: List[HistoryMessage] = None):
        """Appel spécialisé pour les questions de suivi avec gestion d'erreurs et contexte."""
        logger.info("Génération de question de suivi avec Mistral")
        
        if not MISTRAL_API_KEY:
            raise HTTPException(status_code=500, detail="Clé API Mistral manquante")

        system_prompt = self.prompt_service.get_followup_system_prompt()
        
        messages = [{"role": "system", "content": system_prompt}]

        # --- AJOUTÉ : Prise en compte de l'historique pour générer une meilleure question ---
        if history:
            for hist_msg in history:
                messages.append({"role": hist_msg.role, "content": hist_msg.content})
        
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {MISTRAL_API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "mistral-medium-latest",
            "messages": messages,
            "temperature": 0.4,
            "max_tokens": 200
        }
        # ... La logique de try/except reste la même
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(MISTRAL_API_URL, headers=headers, json=payload)
                response.raise_for_status()
                response_data = response.json()
                content = response_data["choices"][0]["message"]["content"]
                return content.strip()
        except Exception as e:
            logger.error(f"Erreur lors de la génération de question de suivi: {str(e)}")
            raise HTTPException(status_code=502, detail=f"Erreur Mistral followup: {str(e)}")

    # --- MODIFIÉ : La signature de la méthode utilise maintenant List[HistoryMessage] ---
    async def _try_with_minimal_model(self, message: str, history: List[HistoryMessage] = None):
        """Tentative avec le modèle le plus économique et des paramètres minimaux."""
        logger.info("Tentative avec paramètres minimaux")
        
        headers = {"Authorization": f"Bearer {MISTRAL_API_KEY}", "Content-Type": "application/json"}
        
        minimal_prompt = self.prompt_service.get_minimal_system_prompt()
        
        messages = [{"role": "system", "content": minimal_prompt}]

        # --- AJOUTÉ : Prise en compte de l'historique même pour le modèle minimal ---
        if history:
            for hist_msg in history:
                messages.append({"role": hist_msg.role, "content": hist_msg.content})

        messages.append({"role": "user", "content": message})
        
        payload = {
            "model": "mistral-small-latest",
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 400
        }
        
        # ... La logique de try/except reste la même
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(MISTRAL_API_URL, headers=headers, json=payload)
                if response.status_code == 200:
                    response_data = response.json()
                    content = response_data["choices"][0]["message"]["content"]
                    logger.info("Succès avec modèle minimal")
                    return content.strip()
                else:
                    raise HTTPException(status_code=429, detail="Service Mistral indisponible.")
        except Exception as e:
            logger.error(f"Échec avec modèle minimal: {str(e)}")
            raise HTTPException(status_code=429, detail="Service Mistral indisponible.")

    def _get_model_for_retry(self, retry_count: int) -> str:
        """Sélectionne le modèle selon le nombre de tentatives"""
        if retry_count == 0:
            return MODEL_NAME or "mistral-large-latest"
        elif retry_count == 1:
            return "mistral-medium-latest"
        else:
            return "mistral-small-latest"

    def get_status(self):
        """Fonction utilitaire pour vérifier le status de l'API"""
        return {
            "api_key_configured": bool(MISTRAL_API_KEY),
            "model": MODEL_NAME,
            "fallback_models": MISTRAL_MODELS
        }