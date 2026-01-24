import asyncio
from surrealdb import AsyncSurreal

async def test_conn():
    url = "ws://localhost:8001/rpc"
    print(f"Testing AsyncSurreal connection to {url}...")
    
    try:
        async with AsyncSurreal(url) as db:
            await db.signin({"user": "root", "pass": "root"})
            await db.use(namespace="test", database="test")
            print("Success with AsyncSurreal context manager!")
            return
    except Exception as e:
        print(f"AsyncSurreal failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_conn())
