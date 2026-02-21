import asyncio
import json
import websockets
import httpx
import sys


async def validate_ui_flow():
    print("🚀 DÉBUT DE LA VALIDATION TDD - UI FLOW (V2)")
    uri = "ws://localhost:8000/ws"
    api_agents = "http://localhost:8000/api/agents"

    results = {
        "websocket_connection": False,
        "health_redis": False,
        "health_llm": False,
        "health_brain": False,
        "agent_discovery_api": [],
        "agent_discovery_ws": [],
        "token_stats_present": False,
    }

    # 1. Tester l'API REST
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(api_agents, timeout=5)
            if resp.status_code == 200:
                agents = resp.json()
                results["agent_discovery_api"] = [a["id"] for a in agents]
    except Exception:
        pass

    # 2. Tester le WebSocket
    try:
        async with websockets.connect(uri) as websocket:
            results["websocket_connection"] = True

            # On attend les heartbeats
            start_time = asyncio.get_event_loop().time()
            while asyncio.get_event_loop().time() - start_time < 30:  # 30s tolerance
                try:
                    raw_msg = await asyncio.wait_for(websocket.recv(), timeout=1)
                    msg = json.loads(raw_msg)

                    if msg.get("type") == "system.status_update":
                        # Handle both flat and nested payloads
                        payload = msg.get("payload", {})
                        if isinstance(payload, str):
                            payload = json.loads(payload)
                        content = payload.get("content", {})
                        if isinstance(content, str):
                            content = json.loads(content)

                        # Component Health
                        comp = content.get("component")
                        status = content.get("status")
                        if comp == "redis" and status == "ok":
                            results["health_redis"] = True
                        if comp == "llm" and status == "ok":
                            results["health_llm"] = True
                        if comp == "brain" and status == "ok":
                            results["health_brain"] = True

                        # Agent Discovery
                        sender = msg.get("sender", {})
                        if isinstance(sender, str):
                            sender = json.loads(sender)
                        aid = sender.get("agent_id")

                        if aid and aid not in ["core", "system", "bridge"] and "status" in content:
                            if aid not in results["agent_discovery_ws"]:
                                results["agent_discovery_ws"].append(aid)
                                print(f"📍 Agent découvert via WS: {aid}")

                            if "total_tokens" in content:
                                results["token_stats_present"] = True
                                print(f"💰 Stats tokens reçues pour {aid}")

                    if results["token_stats_present"] and results["health_brain"]:
                        break
                except Exception:
                    continue
    except Exception as e:
        print(f"❌ WS ERROR: {e}")

    print("\n📊 BILAN FINAL :")
    print(f"Connection WS : {'✅' if results['websocket_connection'] else '❌'}")
    print(
        f"Indicateurs Santé : {'✅' if (results['health_redis'] and results['health_llm'] and results['health_brain']) else '❌'}"
    )
    print(f"Agents (API) : {results['agent_discovery_api']}")
    print(f"Agents (WS) : {results['agent_discovery_ws']} {'✅' if len(results['agent_discovery_ws']) >= 2 else '❌'}")
    print(f"Stats de tokens : {'✅' if results['token_stats_present'] else '❌'}")

    success = results["websocket_connection"] and results["token_stats_present"] and results["health_brain"]
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(validate_ui_flow())
