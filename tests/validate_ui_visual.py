import asyncio
from playwright.async_api import async_playwright
import time

async def test_visual_loop_ui():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("Navigating to hAIrem Bridge...")
        await page.goto("http://localhost:8000")
        
        # Wait a bit for WS to connect
        await asyncio.sleep(5)
        
        test_name = f"ui_test_outfit_{int(time.time())}"
        command = f"/outfit Lisa {test_name}"
        
        print(f"Sending command via UI: {command}")
        # Try different possible selectors for the input
        input_selectors = ["input#chat-input", "#message-input", ".chat-input input", "textarea"]
        input_found = False
        for sel in input_selectors:
            try:
                await page.wait_for_selector(sel, timeout=5000)
                await page.fill(sel, command)
                await page.press(sel, "Enter")
                input_found = True
                break
            except:
                continue
        
        if not input_found:
            print("❌ Could not find chat input field.")
            await page.screenshot(path="nanobanana-output/ui_no_input.png")
            await browser.close()
            return False

        print("Waiting for visual asset to be displayed...")
        # We wait for any image inside the stage or chat area
        try:
            # Increased timeout for generation
            await page.wait_for_selector("img", timeout=60000)
            print("✅ At least one image is now visible in the UI.")
            
            # Take a screenshot
            await page.screenshot(path="nanobanana-output/ui_final_validation.png")
            print("Screenshot saved to nanobanana-output/ui_final_validation.png")
            
            await browser.close()
            return True
        except Exception as e:
            print(f"❌ Failed to detect image in UI: {e}")
            await page.screenshot(path="nanobanana-output/ui_validation_failed.png")
            await browser.close()
            return False

if __name__ == "__main__":
    success = asyncio.run(test_visual_loop_ui())
    if not success:
        exit(1)
