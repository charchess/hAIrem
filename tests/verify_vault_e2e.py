import asyncio
import json
import websockets
import os
import subprocess

async def verify_vault_auto_save():
    # Bridge is on 8000
    uri = "ws://localhost:8000/ws"
    print(f"Connecting to Bridge at {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            test_name = f"test_outfit_{int(asyncio.get_event_loop().time())}"
            
            # 2. Send /outfit command
            msg = {
                "id": "12345678-1234-5678-1234-567812345678",
                "timestamp": "2026-01-28T12:00:00Z",
                "type": "narrative.text",
                "sender": {"agent_id": "user", "role": "user"},
                "recipient": {"target": "Lisa"},
                "payload": {"content": f"/outfit Lisa {test_name}"}
            }
            print(f"Sending: {msg['payload']['content']}")
            await websocket.send(json.dumps(msg))
            
            # 3. Listen for responses
            print("Waiting for visual asset...")
            found_asset = False
            
            try:
                while not found_asset:
                    resp_raw = await asyncio.wait_for(websocket.recv(), timeout=45.0)
                    resp = json.loads(resp_raw)
                    
                    if resp.get("type") == "visual.asset":
                        print(f"✅ Received visual asset: {resp['payload']['content']['url']}")
                        found_asset = True
                    elif resp.get("type") == "narrative.text" and ("échec" in resp['payload']['content'].lower() or "failed" in resp['payload']['content'].lower()):
                        print(f"❌ Error reported by backend: {resp['payload']['content']}")
                        return False
            except asyncio.TimeoutError:
                print("❌ Timed out waiting for generation.")
                return False

            await asyncio.sleep(3)
            
            # 5. Query SurrealDB directly (on port 8001)
            print(f"Verifying vault entry for '{test_name}'...")
            # Use docker exec to avoid local network routing issues if any
            query = f"SELECT * FROM vault WHERE name = '{test_name}';"
            cmd = f"echo \"{query}\" | docker exec -i hairem-surrealdb-1 /surreal sql --endpoint http://localhost:8000 --namespace hairem --database core --user root --pass root"
            
            result = subprocess.check_output(cmd, shell=True).decode()
            print(f"DB Result: {result}")
            
            if test_name in result:
                print("✨ SUCCESS: Vault entry found!")
                return True
            else:
                print("System logs check for VAULT_AUTO_SAVE...")
                logs = subprocess.check_output("docker compose logs --tail=50 h-core", shell=True).decode()
                print(logs)
                return False

    except Exception as e:
        print(f"Test FAILED with exception: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(verify_vault_auto_save())
    if not success:
        exit(1)