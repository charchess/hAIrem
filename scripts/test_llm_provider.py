import asyncio
import os
import sys
from pathlib import Path

# Add apps/h-core to path to import LlmClient
sys.path.append(str(Path(__file__).parent.parent / "apps" / "h-core"))

from src.infrastructure.llm import LlmClient
import litellm

async def test_provider():
    print(f"--- Testing LLM Provider ---")
    print(f"Model: {os.getenv('LLM_MODEL', 'Not Set')}")
    print(f"Base URL: {os.getenv('LLM_BASE_URL', 'Not Set')}")
    
    client = LlmClient()
    messages = [{"role": "user", "content": "Réponds en un mot : es-tu opérationnel ?"}]
    
    print("\nEnvoi de la requête...")
    try:
        response = await client.get_completion(messages)
        print(f"\nRéponse du LLM : {response}")
        print("\n✅ Test réussi !")
    except Exception as e:
        print(f"\n❌ Échec du test : {e}")

if __name__ == "__main__":
    if len(sys.argv) < 1:
        print("Usage: LLM_MODEL=... [LLM_API_KEY=...] python3 scripts/test_llm_provider.py")
    else:
        asyncio.run(test_provider())
