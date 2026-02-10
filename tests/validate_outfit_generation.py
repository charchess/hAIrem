import asyncio
from playwright.async_api import async_playwright
import time
import os

async def validate_outfit_flow():
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
        
        # Ensure Renarde is active (she should be by default)
        
        # Send /outfit command
        # Using a timestamp to ensure uniqueness and avoid cache hits for verification purposes
        test_outfit = f"un bikini sexy {int(time.time())}"
        target_agent = "Renarde"
        command = f"/outfit {target_agent} {test_outfit}"
        
        print(f"⌨️  Typing command: {command}")
        await page.fill("#chat-input", command)
        await page.press("#chat-input", "Enter")
        
        # 1. Check for Ack
        print("🔍 Checking for system acknowledgment...")
        try:
            # Matches: "Je change la tenue de Renarde pour : *un bikini sexy...*"
            await page.wait_for_selector(f"text=Je change la tenue de {target_agent}", timeout=10000)
            print("✅ System ACK received.")
        except Exception as e:
            print(f"❌ System ACK not found: {e}")
            await page.screenshot(path="nanobanana-output/outfit_no_ack.png")
            await browser.close()
            return False

        # 2. Check for Visual Asset Toast
        print("⏳ Waiting for outfit generation (polling Imagen V2)...")
        try:
            # We wait for the toast to appear
            await page.wait_for_selector(".ui-toast", timeout=300000) # 5 mins max
            toast_text = await page.inner_text(".ui-toast")
            print(f"✅ Visual asset TOAST detected: {toast_text}")
        except Exception as e:
            print(f"❌ Visual asset TOAST not detected within timeout: {e}")
            await page.screenshot(path="nanobanana-output/outfit_timeout.png")
            await browser.close()
            return False

        # 3. Verify internal state and DOM
        print("🖼️  Verifying outfit application...")
        await asyncio.sleep(5) # Wait for image load
        
        # Check activeOutfits state in JS
        active_outfit_url = await page.evaluate(f"window.renderer.activeOutfits['{target_agent.lower()}']")
        print(f"👗 Active outfit URL for {target_agent}: {active_outfit_url}")
        
        if not active_outfit_url or "/media/" not in active_outfit_url:
            print("❌ Renderer state does not show a valid generated outfit URL.")
            await browser.close()
            return False
            
        # Check Layer Body
        body_style = await page.evaluate("document.getElementById('layer-agent-body').style.backgroundImage")
        print(f"💃 Current body layer style: {body_style}")
        
        if active_outfit_url in body_style:
            print("✅ Body layer updated with new outfit.")
        else:
            print("⚠️ Body layer style mismatch or update failed.")
            await browser.close()
            return False

        # Take final screenshot
        screenshot_path = "nanobanana-output/outfit_validation_success.png"
        await page.screenshot(path=screenshot_path)
        print(f"✅ Validation successful! Screenshot saved to {screenshot_path}")
        
        await browser.close()
        return True

if __name__ == "__main__":
    if not os.path.exists("nanobanana-output"):
        os.makedirs("nanobanana-output")
        
    success = asyncio.run(validate_outfit_flow())
    if not success:
        print("🛑 Validation FAILED.")
        exit(1)
    else:
        print("🎉 Validation PASSED.")
        exit(0)
