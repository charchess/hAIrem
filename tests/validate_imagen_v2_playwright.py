import asyncio
from playwright.async_api import async_playwright
import time
import os

async def validate_imagen_v2_flow():
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
        
        # Send /imagine command
        test_prompt = f"a stunning cyberpunk landscape {int(time.time())}"
        command = f"/imagine {test_prompt}"
        
        print(f"⌨️  Typing command: {command}")
        await page.fill("#chat-input", command)
        await page.press("#chat-input", "Enter")
        
        # 1. Check for Ack
        print("🔍 Checking for system acknowledgment...")
        try:
            await page.wait_for_selector("text=/J'imagine/", timeout=20000)
            print("✅ System ACK received.")
        except Exception as e:
            print(f"❌ System ACK not found: {e}")
            await page.screenshot(path="nanobanana-output/imagen_v2_no_ack.png")
            await browser.close()
            return False

        # 2. Check for Visual Asset (takes time)
        print("⏳ Waiting for image generation (polling Imagen V2)...")
        # The UI should display a toast: class="ui-toast visible"
        try:
            # We wait for the toast to appear
            await page.wait_for_selector(".ui-toast", timeout=300000) # 5 mins max
            toast_text = await page.inner_text(".ui-toast")
            print(f"✅ Visual asset TOAST detected: {toast_text}")
        except Exception as e:
            print(f"❌ Visual asset TOAST not detected within timeout: {e}")
            await page.screenshot(path="nanobanana-output/imagen_v2_timeout.png")
            await browser.close()
            return False

        # 3. Verify image is actually in the DOM
        print("🖼️  Verifying image element...")
        # Check if the background style contains /media/
        await asyncio.sleep(5) # Wait for fade transition to complete
        
        bg_style = await page.evaluate("document.getElementById('layer-bg').style.backgroundImage")
        print(f"🎨 Current background style: {bg_style}")
        
        if "/media/" in bg_style:
            print("✅ Background updated with generated image.")
        else:
            print("⚠️ Background style does not seem to contain generated image path.")
            # Fallback check on layer-bg-next just in case
            bg_next_style = await page.evaluate("document.getElementById('layer-bg-next').style.backgroundImage")
            print(f"🎨 Next background style: {bg_next_style}")
            if "/media/" in bg_next_style:
                print("✅ Background (next layer) updated with generated image.")
            else:
                print("❌ Failed to verify background update.")
                await browser.close()
                return False
        
        # Take final screenshot
        screenshot_path = "nanobanana-output/imagen_v2_validation_success.png"
        await page.screenshot(path=screenshot_path)
        print(f"✅ Validation successful! Screenshot saved to {screenshot_path}")
        
        await browser.close()
        return True

if __name__ == "__main__":
    if not os.path.exists("nanobanana-output"):
        os.makedirs("nanobanana-output")
        
    success = asyncio.run(validate_imagen_v2_flow())
    if not success:
        print("🛑 Validation FAILED.")
        exit(1)
    else:
        print("🎉 Validation PASSED.")
        exit(0)
