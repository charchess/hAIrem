import asyncio
import json
import websockets
import httpx
import sys
import os


async def validate_product_final():
    print("🚀 DÉBUT DU QUALITY GATE - hAIrem V4.2")
    base_url = "http://localhost:8000"
    ws_uri = "ws://localhost:8000/ws"

    report = {
        "1. REST API Config": False,
        "2. REST API Agents": False,
        "3. WebSocket Connection": False,
        "4. Health Indicators (RD, AI, 🧠)": False,
        "5. Agent Discovery & Skills": False,
        "6. System Logs Flow": False,
    }

    async with httpx.AsyncClient() as client:
        # 1. Test Config API
        try:
            r = await client.get(f"{base_url}/api/config")
            if r.status_code == 200 and "llm_model" in r.json():
                report["1. REST API Config"] = True
                print("✅ Config API: OK")
        except Exception as e:
            print(f"❌ Config API: {e}")

        # 2. Test Agents API
        try:
            r = await client.get(f"{base_url}/api/agents")
            if r.status_code == 200 and len(r.json()) > 0:
                report["2. REST API Agents"] = True
                print(f"✅ Agents API: OK ({len(r.json())} agents found)")
        except Exception as e:
            print(f"❌ Agents API: {e}")

    # 3. Test WebSocket & Real-time Flow
    try:
        async with websockets.connect(ws_uri) as ws:
            report["3. WebSocket Connection"] = True
            print("✅ WebSocket: Connecté")

            # On attend les données pendant 20s
            start = asyncio.get_event_loop().time()
            found_health = False
            found_agents = False
            found_logs = False

            while asyncio.get_event_loop().time() - start < 20:
                try:
                    msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=2))
                    mtype = msg.get("type")
                    content = msg.get("payload", {}).get("content", {})

                    if mtype == "system.heartbeat":
                        if "health" in content:
                            h = content["health"]
                            if h.get("redis") == "ok" and h.get("brain") == "ok":
                                found_health = True
                        if "agents" in content and len(content["agents"]) > 0:
                            found_agents = True

                    if mtype == "system.log":
                        found_logs = True

                    if found_health and found_agents:  # Logs can take time
                        break
                except Exception:
                    continue

            report["4. Health Indicators (RD, AI, 🧠)"] = found_health
            report["5. Agent Discovery & Skills"] = found_agents
            report["6. System Logs Flow"] = found_logs

    except Exception as e:
        print(f"❌ WebSocket Flow: {e}")

    print("\n📊 BILAN QUALITÉ FINAL :")
    for task, status in report.items():
        print(f"{task.ljust(35)} : {'✅' if status else '❌'}")

    success = all(report.values())
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(validate_product_final())
