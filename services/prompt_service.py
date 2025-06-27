# services/prompt_service.py
from typing import Dict, Any, List, Optional
import os
import logging

logger = logging.getLogger(__name__)

class PromptService:
    def __init__(self):
        self.prompts_dir = os.path.join(os.path.dirname(__file__), "../prompts")
        self._cache = {}  # Cache pour éviter de relire les fichiers à chaque fois
        
    def load_prompt(self, name: str) -> str:
        """Charge un prompt depuis un fichier txt avec cache"""
        if name in self._cache:
            return self._cache[name]
            
        try:
            path = os.path.join(self.prompts_dir, f"{name}.txt")
            with open(path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                self._cache[name] = content
                return content
        except FileNotFoundError:
            logger.error(f"Fichier prompt non trouvé: {name}.txt")
            raise FileNotFoundError(f"Prompt '{name}' non trouvé")
        except Exception as e:
            logger.error(f"Erreur lors du chargement du prompt {name}: {str(e)}")
            raise
    
    def get_system_prompt(self) -> str:
        """Récupère le prompt système principal"""
        return self.load_prompt("base_prompt")
    
    def get_minimal_system_prompt(self) -> str:
        """Récupère le prompt système minimal pour les retry"""
        return self.load_prompt("minimal_prompt")
    
    def get_followup_system_prompt(self) -> str:
        """Récupère le prompt système pour les questions de suivi"""
        return self.load_prompt("followup_prompt")
    
    def build_followup_prompt(self, ticket: Dict[str, Any], history: Optional[List[str]] = None) -> str:
        """Construit le prompt complet pour les questions de suivi"""
        
        history_str = "\n".join([f"{msg.role}: {msg.content}" for msg in history]) if history else "Aucun historique."
        
        # Formatage propre du ticket
        ticket_str = "\n".join([f"{k}: {v}" for k, v in ticket.items()])
        
        followup_prompt = self.get_followup_system_prompt

        return (
            f"{followup_prompt}\n"
            f"Historique de la conversation:\n{history_str}\n\n"
            f"Ticket actuel:\n{ticket_str}\n\n"
        )
    
    def invalidate_cache(self):
        """Vide le cache des prompts (utile pour le développement)"""
        self._cache.clear()
        logger.info("Cache des prompts vidé")