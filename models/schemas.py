# models/schemas.py
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional, Dict, Any
from enum import Enum

class TicketCategory(str, Enum):
    """Catégories de tickets disponibles"""
    BUG = "BUG"
    DEMANDE = "DEMANDE"
    INCIDENT = "INCIDENT"
    QUESTION = "QUESTION"
    AUTRE = "AUTRE"

class TicketPriority(str, Enum):
    """Priorités de tickets disponibles"""
    CRITIQUE = "CRITIQUE"
    HAUTE = "HAUTE"
    MOYENNE = "MOYENNE"
    BASSE = "BASSE"

# --- NOUVEAU : Modèle pour l'historique structuré ---
# Ajout d'un modèle pour rendre l'historique plus robuste et explicite
class HistoryMessage(BaseModel):
    """Modèle pour un message dans l'historique de conversation"""
    role: str = Field(..., description="Rôle de l'auteur du message (user ou assistant)")
    content: str = Field(..., description="Contenu du message")

class TicketInput(BaseModel):
    """Schéma pour l'entrée d'analyse de ticket"""
    message: str = Field(..., description="Message du ticket à analyser", min_length=1)
    history: Optional[List[HistoryMessage]] = Field(
        default_factory=list, 
        description="Historique structuré des messages précédents"
    )
    
    # --- MODIFIÉ : Syntaxe du validateur ---
    # @validator devient @field_validator
    @field_validator('message')
    @classmethod
    def validate_message(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Le message ne peut pas être vide')
        return v.strip()
    
    # --- MODIFIÉ : Syntaxe de la configuration ---
    # class Config avec schema_extra est remplacé par model_config avec json_schema_extra
    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "message": "Mon imprimante ne fonctionne plus depuis ce matin",
                "history": [
                    {"role": "user", "content": "Bonjour"},
                    {"role": "assistant", "content": "Bonjour, comment puis-je vous aider ?"}
                ]
            }
        }
    )

class FollowUpInput(BaseModel):
    """Schéma pour la génération de questions de suivi"""
    ticket: Dict[str, Any] = Field(..., description="Ticket partiellement rempli")
    history: Optional[List[HistoryMessage]] = Field(
        default_factory=list,
        description="Historique structuré de la conversation"
    )
    
    @field_validator('ticket')
    @classmethod
    def validate_ticket(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        if not v:
            raise ValueError('Le ticket ne peut pas être vide')
        return v
    
    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "ticket": {
                    "Title": "Problème imprimante",
                    "Category": "INCIDENT",
                    "Priority": "[INCONNU]",
                    "Localisation": "[INCONNU]",
                    "Description": "L'imprimante ne fonctionne plus",
                    "Frustration": 3
                },
                "history": [
                    {"role": "user", "content": "Mon imprimante ne fonctionne plus"}
                ]
            }
        }
    )

class TicketResponse(BaseModel):
    """Schéma pour la réponse d'un ticket analysé"""
    title: str = Field(..., description="Titre du ticket")
    category: TicketCategory = Field(..., description="Catégorie du ticket")
    priority: TicketPriority = Field(..., description="Priorité du ticket")
    localisation: str = Field(..., description="Localisation ou [INCONNU]")
    description: str = Field(..., description="Description du problème")
    frustration: int = Field(..., ge=1, le=5, description="Niveau de frustration (1-5)")
    
    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "title": "Problème d'impression",
                "category": "INCIDENT",
                "priority": "MOYENNE",
                "localisation": "Bureau 204",
                "description": "L'imprimante HP du bureau ne répond plus depuis ce matin",
                "frustration": 3
            }
        }
    )

class ApiResponse(BaseModel):
    """Schéma de réponse standard de l'API"""
    success: bool = Field(..., description="Indique si l'opération a réussi")
    data: Optional[Any] = Field(default=None, description="Données de la réponse")
    message: str = Field(..., description="Message descriptif")
    error: Optional[str] = Field(default=None, description="Message d'erreur si applicable")
    
    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {"question": "Dans quel bureau se trouve l'imprimante ?"},
                "message": "Question générée avec succès",
                "error": None
            }
        }
    )

class HealthResponse(BaseModel):
    """Schéma pour la réponse de santé de l'API"""
    status: str = Field(..., description="Statut général (healthy/unhealthy)")
    backend: str = Field(..., description="Backend utilisé (mistral/ollama)")
    model_service: Optional[Dict[str, Any]] = Field(default=None, description="Statut du service de modèle")
    prompts: Optional[Dict[str, bool]] = Field(default=None, description="Statut des prompts chargés")
    error: Optional[str] = Field(default=None, description="Message d'erreur si applicable")