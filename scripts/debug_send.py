import asyncio
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
        page = await browser.new_page()
        
        # Capture console logs
        page.on("console", lambda msg: print(f"BROWSER CONSOLE: {msg.text}"))
        page.on("pageerror", lambda exc: print(f"BROWSER ERROR: {exc}"))

        print("Navigating to http://localhost:8000...")
        await page.goto("http://localhost:8000")
        
        # Attendre que le websocket soit prêt
        await asyncio.sleep(1)

        # Type a message
        print("Typing 'Hello'...")
        await page.fill("#chat-input", "Hello")
        
        # Click send
        print("Clicking send button...")
        await page.click("#chat-send")
        
        # Attendre pour voir si le message apparaît dans l'historique
        print("Checking history...")
        await asyncio.sleep(1)
        history_content = await page.inner_text("#chat-history")
        print(f"History Content: {history_content.strip()}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
