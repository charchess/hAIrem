import asyncio
import websockets
import json
import uuid

async def test_ws():
    uri = "ws://localhost:8000/ws"
    async with websockets.connect(uri) as websocket:
        print("Connected to WS.")
        
        # Send a narrative message to Electra
        msg = {
            "id": str(uuid.uuid4()),
            "type": "narrative.text",
            "sender": {"agent_id": "user", "role": "user"},
            "recipient": {"target": "Electra"},
            "payload": {"content": "eteins le plafonnier", "format": "text"}
        }
        
        print(f"Sending message: {json.dumps(msg)}")
        await websocket.send(json.dumps(msg))
        
        # Wait for responses
        try:
            while True:
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                data = json.loads(response)
                print(f"Received: {data.get('type')} from {data.get('sender', {}).get('agent_id')}")
                if data.get('type') == 'narrative.text' and data.get('sender', {}).get('agent_id') == 'Electra':
                    print("✅ Electra responded!")
                    print(f"Content: {data.get('payload', {}).get('content')}")
                    break
        except asyncio.TimeoutError:
            print("❌ Timeout waiting for Electra.")

if __name__ == "__main__":
    asyncio.run(test_ws())
