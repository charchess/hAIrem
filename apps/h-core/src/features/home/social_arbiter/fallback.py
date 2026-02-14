from .models import AgentProfile


class FallbackBehavior:
    def __init__(
        self,
        minimum_threshold: float = 0.2,
        default_agent_id: str | None = None,
    ):
        self.minimum_threshold = minimum_threshold
        self.default_agent_id = default_agent_id

    def select_agent(
        self,
        ranked_agents: list[tuple[AgentProfile, float]],
        all_agents: list[AgentProfile],
    ) -> AgentProfile | None:
        if not ranked_agents:
            return self._get_default_agent(all_agents)
        
        top_agent, top_score = ranked_agents[0]
        
        if top_score >= self.minimum_threshold:
            return top_agent
        
        return self._get_default_agent(all_agents)

    def _get_default_agent(self, agents: list[AgentProfile]) -> AgentProfile | None:
        if not agents:
            return None
        
        if self.default_agent_id:
            for agent in agents:
                if agent.agent_id == self.default_agent_id:
                    return agent
        
        active_agents = [a for a in agents if a.is_active]
        if active_agents:
            return min(active_agents, key=lambda a: (a.response_count, a.agent_id))
        
        return min(agents, key=lambda a: (a.response_count, a.agent_id))
