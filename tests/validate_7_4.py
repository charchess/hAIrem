import asyncio
from playwright.async_api import async_playwright
import time

async def validate_navigation():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("Navigating to http://localhost:8000 ...")
        await page.goto("http://localhost:8000")
        
        # 1. Verify default view is Stage
        print("Checking default view (Stage)...")
        dialogue = page.locator("#dialogue-container")
        await dialogue.wait_for(state="visible")
        assert await dialogue.is_visible(), "Dialogue container should be visible in Stage view"
        
        # 2. Switch to Dashboard via Nav Button
        print("Switching to Dashboard view...")
        nav_dashboard = page.locator("#nav-dashboard")
        await nav_dashboard.click()
        
        dashboard = page.locator("#agent-dashboard")
        await dashboard.wait_for(state="visible")
        assert await dashboard.is_visible(), "Dashboard should be visible after switch"
        
        # Wait for fade transition
        await asyncio.sleep(1)
        
        # Check if stage elements are hidden
        # (opacity check might be tricky, checking pointer-events or just assume logic)
        opacity = await dialogue.evaluate("el => window.getComputedStyle(el).opacity")
        assert float(opacity) < 0.1, "Stage elements should be faded out"
        
        # 3. Verify persistence (Reload)
        print("Testing state persistence on reload...")
        await page.reload()
        await dashboard.wait_for(state="visible")
        assert await dashboard.is_visible(), "Dashboard should remain active after reload"
        
        # 4. Switch back to Stage
        print("Switching back to Stage view...")
        nav_stage = page.locator("#nav-stage")
        await nav_stage.click()
        await dialogue.wait_for(state="visible")
        assert await dialogue.is_visible(), "Stage should be visible again"
        
        print("All navigation and polishing validations passed!")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(validate_navigation())
