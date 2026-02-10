import asyncio
from playwright.async_api import async_playwright
import time
import uuid

async def validate_history_recovery():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("Connecting to http://localhost:8000 ...")
        await page.goto("http://localhost:8000")
        
        chat_input = page.locator("#chat-input")
        await chat_input.wait_for()
        
        # 1. Send a unique message
        unique_id = str(uuid.uuid4())[:8]
        test_msg = f"Persistence Test Message {unique_id}"
        print(f"Sending unique message: {test_msg}")
        await chat_input.fill(test_msg)
        await chat_input.press("Enter")
        
        # Wait for bubble to appear locally
        await page.locator(".bubble-user", has_text=test_msg).wait_for(state="visible")
        print("Message appears locally.")
        
        # 2. Reload the page
        print("Reloading page...")
        await page.reload()
        await chat_input.wait_for()
        
        # 3. Verify message is recovered
        print("Checking for recovered message...")
        # Give it a moment to fetch from API
        recovered_bubble = page.locator(".bubble-user", has_text=test_msg)
        
        try:
            await recovered_bubble.wait_for(state="visible", timeout=10000)
            print(f"✅ SUCCESS: Message '{test_msg}' recovered from SurrealDB!")
        except Exception:
            print(f"❌ FAILURE: Message '{test_msg}' not found after reload.")
            # List what we found
            texts = await page.locator(".message-bubble").all_inner_texts()
            print(f"Messages found: {texts}")
            raise Exception("History recovery failed")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(validate_history_recovery())
