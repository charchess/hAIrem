import logging
from src.domain.agent import BaseAgent

logger = logging.getLogger(__name__)


class Agent(BaseAgent):
    def setup(self):
        super().setup()

    async def get_fridge_status(self) -> str:
        return "Le frigo est fermé. Température: 4°C. Contenu estimé: normal."

    async def get_house_status(self) -> str:
        return "Maison: mode normal. Lumières: éteintes. Température ambiante: 21°C. Aucune alerte."

    async def add_reminder(self, memo: str) -> str:
        if not hasattr(self, "_reminders"):
            self._reminders = []
        self._reminders.append(memo)
        return f"Rappel enregistré: {memo}"

    # on_proactive_trigger n'existe pas dans BaseAgent.
    # Pour l'accrocher: surcharger start() ou brancher sur un event Redis custom.
