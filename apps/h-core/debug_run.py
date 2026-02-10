from src.infrastructure.llm import LlmClient
import os

os.environ["LLM_API_KEY"] = "test_key"
client = LlmClient()
print(f"Final api_key type: {type(client.api_key)}")
