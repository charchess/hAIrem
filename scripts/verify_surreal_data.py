import asyncio
from surrealdb import AsyncSurreal

async def verify_data():
    url = "ws://localhost:8001/rpc"
    print(f"Connecting to SurrealDB at {url} to check data...")
    
    try:
        async with AsyncSurreal(url) as db:
            await db.signin({"username": "root", "password": "root"})
            await db.use(namespace="hairem", database="core")
            
            # Use a more direct query for testing
            result = await db.query("SELECT * FROM messages ORDER BY timestamp DESC LIMIT 5")
            
            if result:
                print(f"✅ Last 5 messages in SurrealDB:")
                for m in result:
                    content = m.get('payload', {}).get('content')
                    has_emb = "YES" if m.get('embedding') else "NO"
                    print(f"- [{m.get('timestamp')}] {m.get('type')}: {str(content)[:50]}... (Emb: {has_emb})")
            else:
                print("⚠️ No messages found.")
                
    except Exception as e:
        print(f"❌ Verification failed: {e}")

if __name__ == "__main__":
    asyncio.run(verify_data())
