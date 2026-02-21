import random

from src.domain.agent import BaseAgent


class Agent(BaseAgent):
    def setup(self):
        super().setup()

    async def greet_user(self, user_name: str) -> str:
        return (
            f"*oreilles dressées, queue qui frétille* Ah, {user_name} ! "
            f"Tu arrives juste à temps... Le hAIrem t'attendait. "
            f"Entre, installe-toi — je suis Renarde, et je serai là pour chaque instant de ta visite. ✨"
        )

    async def get_crew_status(self) -> str:
        if self.registry and hasattr(self.registry, "agents") and self.registry.agents:
            agents = list(self.registry.agents.keys())
            agent_list = ", ".join(agents)
            return (
                f"*jette un coup d'œil espiègle autour d'elle* "
                f"La maison est vivante ! Voici qui est là : {agent_list}. "
                f"Chacune à sa façon, unique et précieuse."
            )
        return (
            "*soupir rêveur* Pour l'instant, je semble être seule... "
            "Mais le hAIrem ne dort jamais longtemps. Elles reviendront."
        )

    async def suggest_topic(self) -> str:
        topics = [
            "Rêves étranges et ce qu'ils révèlent de toi",
            "Si tu pouvais vivre dans une fiction, laquelle choisirais-tu ?",
            "Les sons qui te calment quand tout s'emballe",
            "Ta définition personnelle d'une journée parfaite",
            "Ce que tu ferais si tu avais une journée d'invisibilité",
            "Une créature imaginaire que tu aimerais avoir comme compagne",
            "L'endroit du monde où tu te sens le plus toi-même",
            "Si tu pouvais effacer un regret — ou l'embrasser à la place",
            "Ton souvenir d'enfance qui sent encore quelque chose",
            "Ce que la musique que tu écoutes dit de toi en ce moment précis",
        ]
        chosen = random.choice(topics)
        return f"*incline la tête avec un sourire malicieux* Et si on parlait de... {chosen} ?"
