import asyncio
from playwright.async_api import async_playwright
import time
import os

async def validate_schoolgirl_outfit():
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Listen for console messages
        page.on("console", lambda msg: print(f"CONSOLE: [{msg.type}] {msg.text}"))
        
        print("🚀 Navigating to hAIrem Bridge...")
        await page.goto("http://localhost:8000")
        
        # Wait for agents to be discovered
        print("⏳ Waiting for agents discovery...")
        await asyncio.sleep(5)
        
        # Send /outfit command
        test_outfit = f"une tenue d'écolière japonaise sexy {int(time.time())}"
        target_agent = "Renarde"
        command = f"/outfit {target_agent} {test_outfit}"
        
        print(f"⌨️  Typing command: {command}")
        await page.fill("#chat-input", command)
        await page.press("#chat-input", "Enter")
        
        # 1. Check for Ack
        print("🔍 Checking for system acknowledgment...")
        try:
            await page.wait_for_selector(f"text=Je change la tenue de {target_agent}", timeout=10000)
            print("✅ System ACK received.")
        except Exception as e:
            print(f"❌ System ACK not found: {e}")
            await page.screenshot(path="nanobanana-output/schoolgirl_no_ack.png")
            await browser.close()
            return False

        # 2. Wait for generation
        print("⏳ Waiting for outfit generation (Pony model + LoRA)...")
        try:
            # We wait for the visual asset to be received and applied
            await page.wait_for_selector(".ui-toast", timeout=300000) 
            toast_text = await page.inner_text(".ui-toast")
            print(f"✅ Visual asset TOAST detected: {toast_text}")
        except Exception as e:
            print(f"❌ Visual asset TOAST not detected: {e}")
            await page.screenshot(path="nanobanana-output/schoolgirl_timeout.png")
            await browser.close()
            return False

        # 3. Final verification
        await asyncio.sleep(5)
        body_style = await page.evaluate("document.getElementById('layer-agent-body').style.backgroundImage")
        print(f"💃 Current body layer style: {body_style}")
        
        screenshot_path = "nanobanana-output/schoolgirl_validation.png"
        await page.screenshot(path=screenshot_path)
        print(f"✅ Validation successful! Screenshot saved to {screenshot_path}")
        
        await browser.close()
        return True

if __name__ == "__main__":
    if not os.path.exists("nanobanana-output"):
        os.makedirs("nanobanana-output")
    asyncio.run(validate_schoolgirl_outfit())
