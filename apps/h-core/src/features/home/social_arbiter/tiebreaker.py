from .models import AgentProfile


class Tiebreaker:
    @staticmethod
    def apply(agents: list[tuple[AgentProfile, float]]) -> list[tuple[AgentProfile, float]]:
        if len(agents) <= 1:
            return agents
        
        max_score = agents[0][1]
        top_agents = [(a, s) for a, s in agents if abs(s - max_score) < 0.001]
        
        if len(top_agents) <= 1:
            return agents
        
        return sorted(top_agents, key=lambda x: (
            -x[1],
            x[0].response_count,
            - (x[0].last_response_time or 0),
            x[0].agent_id,
        ))
