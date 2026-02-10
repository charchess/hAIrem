import asyncio
from playwright.async_api import async_playwright

async def final_polish_check():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_viewport_size({"width": 1024, "height": 768})
        
        print("Starting Final Polish Check on http://192.168.200.61:8000 ...")
        await page.goto("http://192.168.200.61:8000")
        
        chat_input = page.locator("#chat-input")
        suggestion_menu = page.locator("#suggestion-menu")

        # 1. Test Escape to hide suggestions
        print("Testing Escape key...")
        await chat_input.fill("/")
        await suggestion_menu.wait_for(state="visible")
        await page.keyboard.press("Escape")
        await suggestion_menu.wait_for(state="hidden")
        print("Escape key verified.")

        # 2. Test Agent Tab completion
        print("Testing Agent Tab completion...")
        await chat_input.fill("/Exp")
        await page.keyboard.press("Tab")
        val = await chat_input.input_value()
        assert val == "/Expert-Domotique ", f"Agent tab completion failed: '{val}'"
        print("Agent tab completion verified.")

        # 3. Test Log Pause/Clear
        print("Testing Log Controls...")
        # Since 'L' shortcut might be flaky in some headless environments, 
        # let's trigger it via auto-show or evaluation if needed, 
        # but the prompt asked for shortcut verification.
        # Let's try one more time with explicit focus.
        await page.mouse.click(0, 0)
        await page.keyboard.press("l")
        
        # Wait for hidden class to be removed
        await page.wait_for_function("() => !document.getElementById('log-viewer').classList.contains('hidden')")
        
        log_content = page.locator("#log-content")
        await page.locator("#clear-logs").click()
        assert await log_content.inner_text() == "", "Clear logs failed"
        
        await page.locator("#pause-logs").click()
        # Trigger log
        await page.evaluate("() => window.renderer.addLog('Paused Test')")
        pause_btn = page.locator("#pause-logs")
        assert "paused" in await pause_btn.get_attribute("class"), "Pause button class missing"
        print("Log controls verified.")

        # 4. Dashboard Close Button
        print("Testing Dashboard Close Button...")
        await page.locator("#nav-dashboard").click()
        await page.wait_for_function("() => !document.getElementById('agent-dashboard').classList.contains('hidden')")
        await page.locator("#close-dashboard").click()
        await page.wait_for_function("() => document.getElementById('agent-dashboard').classList.contains('hidden')")
        print("Dashboard close button verified.")

        # 5. Check Layout Overlap (Visual check via snapshot)
        print("Checking for obvious overlap in Dashboard mode...")
        await page.locator("#nav-dashboard").click()
        await asyncio.sleep(1)
        # The history should still be visible (opacity 1)
        history_opacity = await page.evaluate("() => window.getComputedStyle(document.getElementById('chat-history')).opacity")
        assert float(history_opacity) > 0.9, "History should be visible in dashboard mode"
        print("Layout visibility verified.")

        print("\n--- FINAL POLISH VALIDATION: SUCCESS ---")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(final_polish_check())
