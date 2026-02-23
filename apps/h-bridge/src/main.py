import asyncio
import json
import logging
import os
import sys
from typing import Any
from uuid import UUID, uuid4

# Pathing
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)
core_src = os.path.abspath(os.path.join(current_dir, "../../h-core/src"))
if core_src not in sys.path:
    sys.path.insert(0, core_src)

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from infrastructure.redis import RedisClient
from infrastructure.surrealdb import SurrealDbClient
from models.hlink import HLinkMessage, MessageType, Payload, Recipient, Sender

# Services
from services.voice import voice_profile_service
from services.voice_modulation import voice_modulation_service
from services.prosody import prosody_service

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger("BRIDGE")

app = FastAPI(title="hAIrem Bridge")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Paths
public_path = os.getenv("STATIC_PATH", "/app/static")
agents_path = os.getenv("AGENTS_PATH", "/app/agents")

# Global
discovered_agents = {}
active_connections: set[WebSocket] = set()
last_heartbeat = None
redis_client = RedisClient(host=os.getenv("REDIS_HOST", "redis"))
surreal_client = SurrealDbClient(
    url=os.getenv("SURREALDB_URL", "ws://surrealdb:8000/rpc"), user="root", password="root"
)


async def system_stream_worker():
    logger.info("📡 BRIDGE: Stream worker ready.")

    async def handler(data: dict):
        global last_heartbeat
        try:
            msg_type = data.get("type")
            # 1. Broadcast to ALL WebSockets
            msg_json = json.dumps(data)
            for ws in list(active_connections):
                try:
                    await ws.send_text(msg_json)
                except:
                    if ws in active_connections:
                        active_connections.remove(ws)

            # 2. Extract Heartbeat Bundle
            if msg_type == "system.heartbeat":
                last_heartbeat = data
                # logger.info(f"💓 HEARTBEAT: Received and broadcasted. Brain state: {data.get('payload', {}).get('content', {}).get('health', {}).get('brain')}")
                payload = data.get("payload", {})
                if isinstance(payload, str):
                    payload = json.loads(payload)
                content = payload.get("content", {})
                if isinstance(content, str):
                    content = json.loads(content)

                # Update Discovery Cache
                agents = content.get("agents", {})
                for aid, stats in agents.items():
                    discovered_agents[aid] = {
                        "id": aid,
                        "active": stats.get("active"),
                        "llm_model": stats.get("llm_model"),
                        "total_tokens": stats.get("tokens"),
                        "prompt_tokens": stats.get("prompt_tokens"),
                        "completion_tokens": stats.get("completion_tokens"),
                        "cost": stats.get("cost"),
                        "location": stats.get("location"),
                        "preferred_location": stats.get("preferred_location"),
                        "skills": stats.get("skills"),
                    }
        except Exception as e:
            logger.error(f"BRIDGE_WORKER_ERR: {e}")

    await redis_client.listen_stream("system_stream", f"bridge-{uuid4().hex[:4]}", "bridge-1", handler, start_id="$")


@app.on_event("startup")
async def startup():
    await redis_client.connect()
    await surreal_client.connect()
    await voice_profile_service.initialize()
    await voice_modulation_service.initialize()
    await prosody_service.initialize()
    asyncio.create_task(system_stream_worker())


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.add(websocket)
    if last_heartbeat:
        await websocket.send_text(json.dumps(last_heartbeat))
    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"📥 BRIDGE: Received from UI: {data[:100]}...")
            msg = json.loads(data)
            stream = (
                "system_stream"
                if "admin" in msg.get("type", "") or "config" in msg.get("type", "")
                else "conversation_stream"
            )
            logger.info(f"🚀 BRIDGE: Publishing to {stream}")
            await redis_client.publish_event(stream, msg)
    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)
    except Exception as e:
        logger.error(f"WS_ERR: {e}")
        if websocket in active_connections:
            active_connections.remove(websocket)


@app.get("/api/agents")
async def get_agents():
    return list(discovered_agents.values())


@app.get("/api/config")
async def get_config():
    # 1. Try SurrealDB
    db_config = await surreal_client.get_config("system")
    if db_config:
        llm = db_config.get("llm_config", {})
        return {"llm_model": llm.get("model"), "llm_provider": llm.get("provider"), "source": "db"}

    # 2. Fallback to Env
    model = os.getenv("LLM_MODEL", "openrouter/nvidia/nemotron-3-nano-30b-a3b:free")
    provider = "openai"
    if "openrouter" in model.lower() or os.getenv("OPENROUTER_API_KEY"):
        provider = "openrouter"
    elif "ollama" in model.lower():
        provider = "ollama"
    elif "google" in model.lower():
        provider = "google"
    return {"llm_model": model, "llm_provider": provider, "source": "env"}


@app.get("/api/history")
async def get_history():
    if not surreal_client.client:
        return {"messages": [], "status": "connecting"}
    try:
        res = await surreal_client._call("query", "SELECT * FROM fact ORDER BY created_at DESC LIMIT 50;")
        messages = res[0].get("result", []) if res else []
        return {"messages": messages, "status": "ok"}
    except Exception as e:
        logger.error(f"History fail: {e}")
        return {"messages": [], "status": "error"}


@app.get("/", response_class=HTMLResponse)
async def root():
    with open(os.path.join(public_path, "index.html"), "r") as f:
        return f.read()


app.mount("/static", StaticFiles(directory=public_path), name="static")
app.mount("/agents", StaticFiles(directory=agents_path), name="agents")


@app.post("/api/voice/enroll")
async def voice_enroll(payload: dict):
    import base64
    from features.home.voice_recognition.service import VoiceRecognitionService
    from features.home.voice_recognition.models import VoiceEnrollmentRequest

    try:
        audio_bytes = base64.b64decode(payload["audio_data"])
        svc = VoiceRecognitionService(redis_client=redis_client, surreal_client=surreal_client)
        req = VoiceEnrollmentRequest(user_id=payload["user_id"], name=payload["name"], audio_data=audio_bytes)
        profile = await svc.enroll_voice(req)
        return {"status": "enrolled", "user_id": profile.user_id, "name": profile.name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/voice/identify")
async def voice_identify(payload: dict):
    import base64
    from features.home.voice_recognition.service import VoiceRecognitionService
    from features.home.voice_recognition.models import VoiceIdentificationRequest

    try:
        audio_bytes = base64.b64decode(payload["audio_data"])
        svc = VoiceRecognitionService(redis_client=redis_client, surreal_client=surreal_client)
        req = VoiceIdentificationRequest(session_id=payload["session_id"], audio_data=audio_bytes)
        result = await svc.identify_voice(req)
        return result.model_dump(exclude={"embedding", "matched_profile"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/onboarding/start")
async def onboarding_start(payload: dict):
    from features.home.onboarding.service import OnboardingService

    svc = OnboardingService(redis_client=redis_client, surreal_client=surreal_client)
    return await svc.start_interview(payload["user_id"], payload.get("user_name"))


@app.post("/api/onboarding/answer")
async def onboarding_answer(payload: dict):
    from features.home.onboarding.service import OnboardingService

    svc = OnboardingService(redis_client=redis_client, surreal_client=surreal_client)
    return await svc.submit_answer(payload["user_id"], payload["answer"])


@app.get("/api/onboarding/status/{user_id}")
async def onboarding_status(user_id: str):
    from features.home.onboarding.service import OnboardingService

    svc = OnboardingService(redis_client=redis_client, surreal_client=surreal_client)
    onboarded = await svc.is_onboarded(user_id)
    return {"user_id": user_id, "onboarded": onboarded}


@app.get("/api/voice/profiles")
async def voice_profiles():
    from features.home.voice_recognition.repository import VoiceProfileRepository

    try:
        repo = VoiceProfileRepository(surreal_client)
        profiles = await repo.get_all_profiles()
        return {"profiles": [{"user_id": p.get("user_id"), "name": p.get("name")} for p in profiles]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/metrics")
async def get_metrics():
    if not last_heartbeat:
        return {"counters": {}, "histograms": {}}
    content = last_heartbeat.get("payload", {}).get("content", {})
    if isinstance(content, str):
        import json as _json

        content = _json.loads(content)
    return content.get("metrics", {"counters": {}, "histograms": {}})


@app.get("/api/status")
async def get_status():
    return {"status": "ok", "heartbeat": last_heartbeat, "agents": len(discovered_agents)}


_PROVIDERS: list[dict[str, Any]] = [
    {
        "id": "ollama",
        "name": "Ollama (Local)",
        "base_url": "http://localhost:11434",
        "default_model": "llama3.2",
        "models": ["llama3.2", "llama3.1", "mistral", "phi4", "gemma3", "qwen2.5", "deepseek-r1"],
        "requires_key": False,
    },
    {
        "id": "openrouter",
        "name": "OpenRouter",
        "base_url": "https://openrouter.ai/api/v1",
        "default_model": "google/gemini-flash-1.5",
        "models": [
            "google/gemini-flash-1.5",
            "google/gemini-2.0-flash",
            "anthropic/claude-3.5-sonnet",
            "anthropic/claude-3.5-haiku",
            "openai/gpt-4o",
            "openai/gpt-4o-mini",
            "deepseek/deepseek-chat",
            "meta-llama/llama-3.3-70b-instruct",
        ],
        "requires_key": True,
    },
    {
        "id": "openai",
        "name": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
        "requires_key": True,
    },
    {
        "id": "anthropic",
        "name": "Anthropic",
        "base_url": "https://api.anthropic.com",
        "default_model": "claude-3-5-sonnet-20241022",
        "models": ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229"],
        "requires_key": True,
    },
    {
        "id": "google",
        "name": "Google Gemini",
        "base_url": "https://generativelanguage.googleapis.com/v1",
        "default_model": "gemini-2.0-flash",
        "models": ["gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-1.5-flash", "gemini-1.5-pro"],
        "requires_key": True,
    },
    {
        "id": "deepseek",
        "name": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-chat",
        "models": ["deepseek-chat", "deepseek-reasoner"],
        "requires_key": True,
    },
    {
        "id": "mistral",
        "name": "Mistral AI",
        "base_url": "https://api.mistral.ai/v1",
        "default_model": "mistral-large-latest",
        "models": ["mistral-large-latest", "mistral-medium-latest", "mistral-small-latest", "codestral-latest"],
        "requires_key": True,
    },
    {
        "id": "azure",
        "name": "Azure OpenAI",
        "base_url": None,
        "default_model": "gpt-4",
        "models": ["gpt-4", "gpt-4o", "gpt-4-turbo"],
        "requires_key": True,
    },
]


@app.get("/api/admin/providers")
async def get_providers():
    return {"providers": _PROVIDERS}


@app.post("/api/admin/test-connection")
async def test_connection(payload: dict):
    import httpx as _httpx

    provider = payload.get("provider", "")
    base_url = payload.get("base_url", "").rstrip("/")
    api_key = payload.get("api_key", "")

    if not base_url:
        prov = next((p for p in _PROVIDERS if p["id"] == provider), None)
        base_url = (prov or {}).get("base_url") or ""

    if not base_url:
        return {"success": False, "message": "No base URL configured for this provider"}

    try:
        async with _httpx.AsyncClient(timeout=5.0) as client:
            if provider == "ollama":
                resp = await client.get(f"{base_url}/api/tags")
                if resp.status_code == 200:
                    data = resp.json()
                    model_names = [m.get("name") for m in data.get("models", [])]
                    return {
                        "success": True,
                        "message": f"Ollama reachable — {len(model_names)} models found",
                        "models": model_names,
                    }
                return {"success": False, "message": f"Ollama returned HTTP {resp.status_code}"}
            else:
                headers = {}
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"
                resp = await client.get(base_url, headers=headers)
                reachable = resp.status_code < 500
                return {
                    "success": reachable,
                    "message": f"Endpoint reachable (HTTP {resp.status_code})"
                    if reachable
                    else f"Endpoint error (HTTP {resp.status_code})",
                }
    except Exception as e:
        return {"success": False, "message": f"Connection failed: {e}"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
