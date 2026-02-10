import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

print("Listing accessible models:")
try:
    for m in genai.list_models():
        if 'image' in m.name or 'imagen' in m.name:
            print(f" - {m.name} (Supported: {m.supported_generation_methods})")
except Exception as e:
    print(f"Error: {e}")
