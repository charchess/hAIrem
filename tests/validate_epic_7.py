import asyncio
from playwright.async_api import async_playwright
import httpx
import time

async def validate_epic_7():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("\n--- Starting Epic 7 Full Validation ---\n")
        print("Navigating to http://localhost:8000 ...")
        await page.goto("http://localhost:8000")
        
        chat_input = page.locator("#chat-input")
        await chat_input.wait_for()

        # STORY 7.1: Slash Commands
        print("\n[7.1] Testing slash commands...")
        await chat_input.fill("/")
        suggestion_menu = page.locator("#suggestion-menu")
        await suggestion_menu.wait_for(state="visible")
        
        items = await page.locator(".suggestion-item").all()
        agent_names = [await item.locator("span:first-child").inner_text() for item in items]
        print(f"Found agents: {agent_names}")
        assert "Renarde" in agent_names, "Renarde missing from suggestions"

        await page.keyboard.press("ArrowDown")
        await page.keyboard.press("Enter")
        
        # Test command suggestions (triggering updateSuggestions)
        await suggestion_menu.wait_for(state="visible")
        cmd_items = await page.locator(".suggestion-item").all()
        cmd_names = [await item.locator("span:first-child").inner_text() for item in cmd_items]
        print(f"Found commands: {cmd_names}")
        assert "ping" in cmd_names, "ping command missing"

        # Tab completion
        await chat_input.fill("/Renarde pi")
        await page.keyboard.press("Tab")
        val = await chat_input.input_value()
        assert "ping " in val, "Tab completion failed"
        print("Story 7.1 PASS")

        # STORY 7.2: System Logs
        print("\n[7.2] Testing system logs...")
        # Open via click or ensure it auto-shows on error
        print("Triggering debug error...")
        async with httpx.AsyncClient() as client:
            await client.get("http://localhost:8000/api/debug/error")
        
        log_viewer = page.locator("#log-viewer")
        await log_viewer.wait_for(state="visible", timeout=5000)
        
        error_line = page.locator("#log-content .log-error")
        await error_line.wait_for(state="visible", timeout=5000)
        assert "CRITICAL_SYSTEM_FAILURE" in await error_line.inner_text()
        print("Story 7.2 PASS")

        # STORY 7.3: Agent Dashboard
        print("\n[7.3] Testing agent dashboard cards...")
        # Toggle dashboard via Nav Button
        await page.locator("#nav-dashboard").click()
        dashboard = page.locator("#agent-dashboard")
        await dashboard.wait_for(state="visible")
        
        agent_cards = page.locator(".agent-card")
        count = await agent_cards.count()
        print(f"Found {count} agent cards.")
        assert count > 0, "No agent cards rendered"
        
        # Verify status update transition
        print("Testing real-time status update...")
        await page.locator("#nav-stage").click() # Close dashboard to talk
        await chat_input.fill("Hello Renarde")
        await chat_input.press("Enter")
        await page.locator("#nav-dashboard").click() # Re-open dashboard
        
        renarde_card = page.locator(".agent-card", has_text="Renarde")
        status_badge = renarde_card.locator(".agent-status-badge")
        
        found_thinking = False
        for _ in range(10):
            text = await status_badge.inner_text()
            if "thinking" in text.lower():
                found_thinking = True
                break
            await asyncio.sleep(0.5)
        assert found_thinking, "Renarde should be thinking"
        print("Story 7.3 PASS")

        # STORY 7.4: Navigation & Switcher
        print("\n[7.4] Testing navigation and layout switching...")
        nav_stage = page.locator("#nav-stage")
        nav_dashboard = page.locator("#nav-dashboard")
        dialogue = page.locator("#dialogue-container")

        print("Switching to Stage...")
        await nav_stage.click()
        await dialogue.wait_for(state="visible")
        assert await dialogue.is_visible()
        
        print("Switching to Dashboard...")
        await nav_dashboard.click()
        await dashboard.wait_for(state="visible")
        
        await asyncio.sleep(1) # Wait for fade
        opacity = await dialogue.evaluate("el => window.getComputedStyle(el).opacity")
        assert float(opacity) < 0.1, "Stage should be hidden"
        
        print("Testing reload persistence...")
        await page.reload()
        await dashboard.wait_for(state="visible")
        assert await dashboard.is_visible(), "Should stay on Dashboard after reload"
        print("Story 7.4 PASS")

        print("\n--- ALL EPIC 7 STORIES VALIDATED SUCCESSFULLY ---\n")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(validate_epic_7())
