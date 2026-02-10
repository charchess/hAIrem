import asyncio
from playwright.async_api import async_playwright

async def validate_gemini_ui():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("Connecting to http://localhost:8000 ...")
        await page.goto("http://localhost:8000")
        
        chat_input = page.locator("#chat-input")
        await chat_input.wait_for()
        
        # Send a message to trigger Renarde (Gemini)
        test_message = "Renarde, es-tu là ? Réponds par une phrase courte pour confirmer ta présence."
        print(f"Sending message: {test_message}")
        await chat_input.fill(test_message)
        await chat_input.press("Enter")
        
        # Wait for the response in history
        print("Waiting for Renarde's response (this can take time with Gemini)...")
        
        # We look for a bubble that is not the first user bubble
        # and has been added AFTER our send.
        found_response = False
        for _ in range(60): # 30s
            bubbles = await page.locator(".bubble-agent").all()
            for b in bubbles:
                text = await b.inner_text()
                # Initial message is about 'Historique de chat activé'
                if "Historique" not in text and len(text.strip()) > 10:
                    print(f"Agent response detected: {text}")
                    found_response = True
                    break
            if found_response: break
            await asyncio.sleep(0.5)
        
        if found_response:
            print("\n✅ End-to-End Gemini Validation SUCCESS!")
        else:
            print("\n❌ End-to-End Validation FAILED: Response not received or incorrect.")
            # Let's see what we got instead
            all_messages = await page.locator(".bubble-agent").all_inner_texts()
            print(f"All agent messages received: {all_messages}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(validate_gemini_ui())
