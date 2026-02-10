import asyncio
import os
from playwright.async_api import async_playwright
import httpx
import time

async def validate_epic_7():
    target_url = os.getenv("APP_URL", "http://localhost:8000")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("\n--- Starting Epic 7 Full Validation ---\n")
        print(f"Navigating to {target_url} ...")
        
        # Capture console logs
        page.on("console", lambda msg: print(f"BROWSER CONSOLE: {msg.text}"))
        
        await page.goto(target_url)
        
        chat_input = page.locator("#chat-input")
        await chat_input.wait_for()

        # STORY 7.1: Slash Commands
        print("\n[7.1] Testing slash commands...")
        await chat_input.fill("/")
        
        # Test agent suggestions
        suggestion_menu = page.locator("#suggestion-menu")
        await suggestion_menu.wait_for(state="visible")
        cmd_items = await page.locator(".suggestion-item").all()
        cmd_names = [await item.locator("span:first-child").inner_text() for item in cmd_items]
        print(f"Found agents: {cmd_names}")
        assert "Renarde" in cmd_names, "Renarde agent missing from suggestions"

        # Tab completion to select agent and show commands
        # Select Renarde (assuming it's in the list, filtering by typing more)
        await chat_input.type("Renarde", delay=50)
        # Wait for filtering to leave only Renarde (or similar)
        await page.locator(".suggestion-item:has-text('Renarde')").wait_for(state="visible")
        await page.keyboard.press("Tab")
        
        # Now we should have "/Renarde " and see commands
        await asyncio.sleep(0.5) # Wait for UI update
        val = await chat_input.input_value()
        assert "/Renarde " in val, f"Agent selection failed. Got: {val}"
        
        # Check for commands
        # Bug Fix Verification: Renarde's command list should now be populated
        try:
            await page.locator(".suggestion-item:has-text('ping')").wait_for(state="visible", timeout=5000)
        except Exception:
            print("DEBUG: Suggestion menu content (Commands step):")
            print(await suggestion_menu.inner_html())
            raise
        print("Found 'ping' command for Renarde.")
        
        # Complete command
        await chat_input.type("pi", delay=50)
        await page.keyboard.press("Tab")
        await asyncio.sleep(0.1)
        val = await chat_input.input_value()
        assert "ping " in val, f"Command completion failed. Got: '{val}'"
        print("Story 7.1 PASS")

        # STORY 7.2: System Logs
        print("\n[7.2] Testing system logs...")
        # Open via click or ensure it auto-shows on error
        print("Triggering debug error...")
        async with httpx.AsyncClient() as client:
            await client.get(f"{target_url}/api/debug/error")
        
        log_viewer = page.locator("#log-viewer")
        await log_viewer.wait_for(state="visible", timeout=5000)
        
        error_line = page.locator("#log-content .log-error")
        await error_line.wait_for(state="visible", timeout=5000)
        assert "CRITICAL_SYSTEM_FAILURE" in await error_line.inner_text()
        print("Story 7.2 PASS")
        
        # Close logs for next tests
        await page.locator("#close-logs").click()
        await log_viewer.wait_for(state="hidden")

        # STORY 7.3: Agent Dashboard
        print("\n[7.3] Testing agent dashboard cards...")
        # Toggle dashboard via Nav Button
        await page.locator("#nav-crew").click()
        dashboard = page.locator("#crew-panel")
        await dashboard.wait_for(state="visible")
        
        agent_cards = page.locator(".agent-card")
        count = await agent_cards.count()
        print(f"Found {count} agent cards.")
        assert count > 0, "No agent cards rendered"
        
        # Verify status update transition
        print("Testing real-time status update...")
        # Note: In new UI, clicking the button again might close it or we use close button
        await page.locator("#close-crew").click() 
        await chat_input.fill("Hello Renarde")
        await chat_input.press("Enter")
        await page.locator("#nav-crew").click() # Re-open
        
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
        nav_admin = page.locator("#nav-admin")
        nav_crew = page.locator("#nav-crew")
        dialogue = page.locator("#dialogue-container")

        print("Opening Admin Panel...")
        await nav_admin.click()
        admin_panel = page.locator("#admin-panel")
        await admin_panel.wait_for(state="visible")
        assert await admin_panel.is_visible()
        
        print("Closing Admin Panel...")
        await page.locator("#close-admin").click()
        await admin_panel.wait_for(state="hidden")

        print("Opening Crew Management...")
        await nav_crew.click()
        await dashboard.wait_for(state="visible")
        
        print("Testing log viewer toggle via key 'L'...")
        await page.keyboard.press("l")
        await log_viewer.wait_for(state="visible")
        await page.keyboard.press("l")
        await log_viewer.wait_for(state="hidden")

        print("\n--- ALL EPIC 7 STORIES VALIDATED SUCCESSFULLY ---\n")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(validate_epic_7())
