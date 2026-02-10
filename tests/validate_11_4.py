import asyncio
import os
from playwright.async_api import async_playwright

async def validate_11_4():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        url = "http://localhost:8080"
        print(f"Navigating to {url}...")
        try:
            await page.goto(url)
        except Exception as e:
            print(f"Failed to connect to {url}: {e}")
            await browser.close()
            return

        # 1. Check default background
        bg_layer = page.locator("#layer-bg")
        bg_style = await bg_layer.get_attribute("style")
        print(f"Background Style: {bg_style}")
        assert "background.png" in bg_style, "Default background not loaded"

        # 2. Check initial agent pose (Renarde/test_model)
        body_layer = page.locator("#layer-agent-body")
        body_style = await body_layer.get_attribute("style")
        print(f"Initial Body Style: {body_style}")
        assert "test_model_neutral_01.png" in body_style, "Initial pose not loaded correctly"

        # 3. Inject a message with a pose tag (Testing French Alias)
        print("Injecting message with [pose:triste]...")
        await page.evaluate("""
            window.network.handleMessage({
                type: 'narrative.text',
                sender: { agent_id: 'Renarde', role: 'agent' },
                recipient: { target: 'user' },
                payload: { content: 'Je suis très triste ! [pose:triste]' }
            });
        """)

        # Wait for potential animations
        await asyncio.sleep(2)

        # 4. Check if pose changed (Should map to 'sad')
        body_style_after = await body_layer.get_attribute("style")
        print(f"Body Style After [pose:triste]: {body_style_after}")
        assert "test_model_sad_01.png" in body_style_after, "Pose did not update to sad (alias check failed)"

        # 5. Check if tag is hidden in history
        history = page.locator("#chat-history")
        history_text = await history.inner_text()
        print(f"History Text: {history_text}")
        assert "[pose:triste]" not in history_text, "Pose tag still visible in history"
        assert "Je suis très triste !" in history_text, "Cleaned text missing from history"

        print("SUCCESS: 11.4 Validation Passed.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(validate_11_4())
