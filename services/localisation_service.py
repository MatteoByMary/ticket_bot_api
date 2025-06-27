# services/location_service.py
import pandas as pd
from thefuzz import process
import logging
import os

logger = logging.getLogger(__name__)

class LocationService:
    # La seule ligne modifiée est le chemin par défaut du fichier.
    def __init__(self, file_path: str = 'data/localisations.xlsx'):
        """
        Initialise le service de localisation.
        
        Args:
            file_path (str): Chemin relatif vers le fichier Excel depuis la racine du projet.
        """
        self.file_path = file_path
        self._cache = []
        self.load_locations()

    def load_locations(self):
        """
        Charge les localisations depuis le fichier Excel en mémoire.
        """
        try:
            # Construit le chemin absolu à partir de la racine du projet
            # Le chemin de base __file__ est /services/location_service.py
            # os.path.dirname(__file__) -> /services
            # os.path.dirname(os.path.dirname(__file__)) -> / (racine du projet)
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            absolute_path = os.path.join(project_root, self.file_path)

            if not os.path.exists(absolute_path):
                 raise FileNotFoundError(f"Fichier non trouvé à l'emplacement: {absolute_path}")

            df = pd.read_excel(absolute_path)
            if 'Etablissement' not in df.columns:
                raise KeyError("La colonne 'Etablissement' est introuvable dans le fichier Excel.")
            
            self._cache = df['Etablissement'].dropna().tolist()
            logger.info(f"✅ {len(self._cache)} localisations chargées depuis {self.file_path}")
        except FileNotFoundError as e:
            logger.error(f"⚠️ {e}. Le service de localisation sera inactif.")
            self._cache = []
        except KeyError as e:
            logger.error(f"⚠️ Erreur de configuration Excel: {e}. Le service de localisation sera inactif.")
            self._cache = []
        except Exception as e:
            logger.error(f"⚠️ Une erreur inattendue est survenue lors du chargement des localisations: {e}")
            self._cache = []

    def find_best_match(self, user_location: str, score_cutoff: int = 80) -> str | None:
        """
        Trouve la meilleure correspondance pour une localisation donnée.

        Args:
            user_location (str): La localisation brute à rechercher.
            score_cutoff (int): Le score de similarité minimum (0-100) pour une correspondance valide.

        Returns:
            str | None: Le nom officiel de la localisation ou None si aucune correspondance satisfaisante n'est trouvée.
        """
        if not user_location or not self._cache:
            return None

        best_match = process.extractOne(user_location, self._cache)

        if best_match:
            official_name, score = best_match
            if score >= score_cutoff:
                logger.info(f"Correspondance de localisation trouvée pour '{user_location}' -> '{official_name}' (Score: {score}%)")
                return official_name
            else:
                logger.info(f"Correspondance pour '{user_location}' rejetée. Score ({score}%) trop bas (seuil: {score_cutoff}%)")
        
        return None