from src.domain.agent import BaseAgent

class Agent(BaseAgent):
    def setup(self):
        super().setup()
        self.register_command("hello_dummy", self._handle_hello)
        
    async def _handle_hello(self, payload):
        return "Hello from Dummy Agent"
