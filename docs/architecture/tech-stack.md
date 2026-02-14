# Technology Stack

## Core Backend
*   **Language:** Python 3.11+
*   **Framework:** FastAPI (pour les APIs et services)
*   **Asynchronous Runtime:** `asyncio`

## Data & Persistence
*   **Database:** SurrealDB (Graph Mode enabled for Cognitive Architecture)
*   **Message Bus:** Redis 7.x (Pub/Sub for event broadcasting)

## AI & Cognitive Services
*   **Inference Orchestration:** LiteLLM (Supports Local, Remote GPU, and Cloud providers)
*   **LLM Providers (Modular):**
    *   **Cloud:** OpenRouter, Gemini, Grok, OpenAI, Anthropic
    *   **Local:** Ollama, LM Studio, Oobabooga (via LiteLLM)
*   **Image Generation (Modular):**
    *   **Primary:** NanoBanana (ComfyUI-based)
    *   **Secondary:** Imagen (projet connexe)
    *   **Others:** Configurable via LiteLLM-like abstraction
*   **Image Processing:** `rembg` (La Découpeuse - Background removal)
*   **Speech-to-Text (STT):** Whisper (Local execution or Dockerized)
*   **Text-to-Speech (TTS - Modular):**
    *   **Primary:** MeloTTS (Open Source, local)
    *   **Secondary:** OpenVoice (voice cloning)
    *   **Cloud Fallback:** ElevenLabs (high quality)
*   **Voice Modulation:** Prosody/intonation injection via LLM

## Tooling & Quality
*   **Linting/Formatting:** Ruff
*   **Type Checking:** Mypy
*   **Testing:** Pytest
*   **Package Management:** Poetry / standard pip (pyproject.toml)

## Infrastructure
*   **Containerization:** Docker & Docker Compose
*   **OS Environment:** Linux (optimized for production)
