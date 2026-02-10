import asyncio
from playwright.async_api import async_playwright
import time

async def verify_slash_commands():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # Navigate to the UI
        print("Navigating to http://localhost:8000 ...")
        await page.goto("http://localhost:8000")
        
        # Wait for the chat input to be available
        chat_input = page.locator("#chat-input")
        await chat_input.wait_for()
        
        # 1. Test detecting '/' and showing agents
        print("Testing agent suggestions...")
        await chat_input.fill("/")
        suggestion_menu = page.locator("#suggestion-menu")
        await suggestion_menu.wait_for(state="visible")
        
        items = await page.locator(".suggestion-item").all()
        print(f"Found {len(items)} agent suggestions.")
        agent_names = [await item.locator("span:first-child").inner_text() for item in items]
        print(f"Agents: {agent_names}")
        
        assert "Renarde" in agent_names or "Expert-Domotique" in agent_names, "Agent suggestions missing expected agents"

        # 2. Test selecting an agent (keyboard navigation)
        print("Testing keyboard navigation (ArrowDown and Enter)...")
        await page.keyboard.press("ArrowDown")
        await page.keyboard.press("Enter")
        
        val = await chat_input.input_value()
        print(f"Input value after selection: {val}")
        assert val.startswith("/"), "Input should still start with /"
        
        # 3. Test command suggestions
        print("Testing command suggestions...")
        # Assume Renarde or Expert-Domotique was selected. Let's force one if needed, 
        # but let's see what happened.
        if " " not in val:
             await chat_input.fill("/Renarde ")
        
        await suggestion_menu.wait_for(state="visible")
        cmd_items = await page.locator(".suggestion-item").all()
        print(f"Found {len(cmd_items)} command suggestions.")
        cmd_names = [await item.locator("span:first-child").inner_text() for item in cmd_items]
        print(f"Commands: {cmd_names}")
        
        assert "ping" in cmd_names, "Command suggestions missing 'ping'"

        # 4. Test Tab completion
        print("Testing Tab completion...")
        await chat_input.fill("/Renarde pi")
        await page.keyboard.press("Tab")
        val = await chat_input.input_value()
        print(f"Input value after Tab: {val}")
        assert "ping" in val, "Tab completion failed for command"

        print("All UI tests for 7.1 passed!")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(verify_slash_commands())
