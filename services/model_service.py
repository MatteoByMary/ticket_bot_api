# services/model_service.py
import requests
import json
from fastapi import HTTPException
from typing import List, Optional
from models.schemas import HistoryMessage
import logging

logger = logging.getLogger(__name__)

class ModelService:
    def __init__(self, backend: str, ollama_url: str, ollama_model: str, prompt_service):
        self.backend = backend
        self.ollama_url = ollama_url
        self.ollama_model = ollama_model
        self.prompt_service = prompt_service
        
        # Validation du backend au démarrage
        if backend not in ["mistral", "ollama"]:
            raise ValueError(f"Backend non supporté: {backend}")
        
        # Initialisation des services spécialisés
        if backend == "mistral":
            from .model_mistral import MistralService
            self.mistral_service = MistralService(prompt_service)
        
        logger.info(f"ModelService initialisé avec backend: {backend}")
    
    async def analyze_ticket(self, message: str, history: Optional[List[HistoryMessage]] = None) -> str:
        """Analyse un message et génère un ticket"""
        try:
            if self.backend == "mistral":
                return await self.mistral_service.analyze_ticket(message, history)
            elif self.backend == "ollama":
                return await self._call_ollama_analyze(message, history)
            else:
                raise HTTPException(status_code=400, detail="Backend non supporté")
        except Exception as e:
            logger.error(f"Erreur dans analyze_ticket: {str(e)}")
            raise
    
    async def generate_followup(self, prompt: str, history: Optional[List[HistoryMessage]] = None) -> str:
        """Génère une question de suivi"""
        try:
            if self.backend == "mistral":
                return await self.mistral_service.generate_followup(prompt, history)
            elif self.backend == "ollama":
                return await self._call_ollama_followup(prompt)
            else:
                raise HTTPException(status_code=400, detail="Backend non supporté")
        except Exception as e:
            logger.error(f"Erreur dans generate_followup: {str(e)}")
            raise
    
    async def _call_ollama_analyze(self, message: str, history: Optional[List[str]] = None) -> str:
        """Appel à Ollama pour l'analyse"""
        try:
            # Utilisation du prompt depuis le fichier
            base_prompt = self.prompt_service.get_system_prompt()
            
            conversation = "\n".join(history + [message]) if history else message
            
            payload = {
                "model": self.ollama_model,
                "prompt": f"{base_prompt}\n\nMessage de l'utilisateur:\n{conversation}",
                "temperature": 0.2,
                "top_p": 0.95,
                "stream": False
            }
            
            return await self._make_ollama_request(payload)
        except Exception as e:
            logger.error(f"Erreur lors de l'appel Ollama analyze: {str(e)}")
            raise
    
    async def _call_ollama_followup(self, prompt: str) -> str:
        """Appel à Ollama pour le suivi"""
        try:
            # Utilisation du prompt système pour les questions de suivi
            system_prompt = self.prompt_service.get_followup_system_prompt()
            
            payload = {
                "model": self.ollama_model,
                "prompt": f"{system_prompt}\n\n{prompt}",
                "temperature": 0.3,
                "top_p": 0.95,
                "stream": False
            }
            
            return await self._make_ollama_request(payload)
        except Exception as e:
            logger.error(f"Erreur lors de l'appel Ollama followup: {str(e)}")
            raise
    
    async def _make_ollama_request(self, payload: dict) -> str:
        """Effectue la requête HTTP vers Ollama"""
        try:
            response = requests.post(
                self.ollama_url, 
                json=payload, 
                timeout=30,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "").strip()
            
        except requests.exceptions.Timeout:
            logger.error("Timeout lors de l'appel à Ollama")
            raise HTTPException(status_code=504, detail="Timeout du service Ollama")
        except requests.exceptions.ConnectionError:
            logger.error("Impossible de se connecter à Ollama")
            raise HTTPException(status_code=502, detail="Service Ollama indisponible")
        except requests.exceptions.HTTPError as e:
            logger.error(f"Erreur HTTP Ollama: {e}")
            raise HTTPException(status_code=502, detail=f"Erreur Ollama: {e}")
        except Exception as e:
            logger.error(f"Erreur inattendue Ollama: {e}")
            raise HTTPException(status_code=502, detail=f"Erreur Ollama: {e}")
    
    def get_status(self):
        """Retourne le statut du service"""
        status = {
            "backend": self.backend,
            "ollama_url": self.ollama_url if self.backend == "ollama" else None,
            "ollama_model": self.ollama_model if self.backend == "ollama" else None
        }
        
        if self.backend == "mistral" and hasattr(self, 'mistral_service'):
            status.update(self.mistral_service.get_status())
        
        return status