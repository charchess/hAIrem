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
*   **Speech-to-Text (STT):** Whisper (Local execution or Dockerized)
*   **Text-to-Speech (TTS):** 
    *   Piper (Local, low latency)
    *   ElevenLabs (Cloud Hybrid, high quality)

## Tooling & Quality
*   **Linting/Formatting:** Ruff
*   **Type Checking:** Mypy
*   **Testing:** Pytest
*   **Package Management:** Poetry / standard pip (pyproject.toml)

## Infrastructure
*   **Containerization:** Docker & Docker Compose
*   **OS Environment:** Linux (optimized for production)
