import asyncio
from playwright.async_api import async_playwright
import time

async def validate_agent_dashboard():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("Navigating to http://localhost:8000 ...")
        await page.goto("http://localhost:8000")
        
        # 1. Verify Dashboard can be toggled
        print("Testing dashboard toggle (shortcut 'D')...")
        dashboard = page.locator("#agent-dashboard")
        await page.keyboard.press("d")
        await dashboard.wait_for(state="visible")
        assert await dashboard.is_visible(), "Dashboard should be visible after pressing 'D'"
        
        # 2. Check if agent cards are rendered
        print("Checking agent cards...")
        agent_cards = page.locator(".agent-card")
        await agent_cards.first.wait_for(state="visible", timeout=5000)
        count = await agent_cards.count()
        print(f"Found {count} agent cards.")
        assert count > 0, "At least one agent card should be rendered"
        
        # 3. Verify status update (Thinking)
        print("Testing status update UI...")
        # We send a message to Renarde to trigger thinking
        chat_input = page.locator("#chat-input")
        await chat_input.fill("Hello Renarde")
        await chat_input.press("Enter")
        
        # Check for 'thinking' status on Renarde card
        renarde_card = page.locator(".agent-card", has_text="Renarde")
        status_badge = renarde_card.locator(".agent-status-badge")
        
        # It might take a moment to transition to thinking
        await status_badge.wait_for(state="visible")
        # We might need a retry loop or wait for specific text
        found_thinking = False
        for _ in range(10):
            text = await status_badge.inner_text()
            if "thinking" in text.lower():
                found_thinking = True
                break
            await asyncio.sleep(0.5)
            
        assert found_thinking, "Renarde status should transition to 'thinking'"
        print("Renarde 'thinking' status verified.")
        
        # 4. Wait for it to return to idle
        found_idle = False
        for _ in range(60): # 30s timeout
            text = await status_badge.inner_text()
            if "idle" in text.lower():
                found_idle = True
                break
            await asyncio.sleep(0.5)
            
        assert found_idle, "Renarde status should return to 'idle'"
        print("Renarde returned to 'idle' verified.")

        print("All agent dashboard validations passed!")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(validate_agent_dashboard())
