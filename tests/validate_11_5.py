import asyncio
import os
from playwright.async_api import async_playwright

async def validate_11_5():
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

        # Wait for metadata to load (which populates window.renderer.agents)
        print("Waiting for agent metadata...")
        await page.wait_for_function("window.renderer && Object.keys(window.renderer.agents).length > 0")

        # 1. Inject a message from "Dieu" (non-personified)
        print("Injecting message from Dieu (personified: false)...")
        await page.evaluate("""
            window.network.handleMessage({
                id: 'test-dieu-msg',
                type: 'narrative.text',
                sender: { agent_id: 'Dieu', role: 'system' },
                recipient: { target: 'user' },
                payload: { content: "Je suis l'esprit de la maison." }
            });
        """)

        # Wait for potential animations
        await asyncio.sleep(2)

        # 2. Check if agent layers are hidden
        body_layer = page.locator("#layer-agent-body")
        body_style = await body_layer.get_attribute("style")
        print(f"Dieu Body Style: {body_style}")
        assert "display: none" in body_style, "Body layer should be hidden for non-personified agent"

        # 3. Inject a message from "Renarde" (personified)
        print("Injecting message from Renarde (personified: true)...")
        await page.evaluate("""
            window.network.handleMessage({
                id: 'test-renarde-msg',
                type: 'narrative.text',
                sender: { agent_id: 'Renarde', role: 'agent' },
                recipient: { target: 'user' },
                payload: { content: "Salut !" }
            });
        """)

        await asyncio.sleep(2)

        # 4. Check if layers are visible again
        body_style_after = await body_layer.get_attribute("style")
        print(f"Renarde Body Style: {body_style_after}")
        assert "display: block" in body_style_after, "Body layer should be visible for personified agent"

        print("SUCCESS: 11.5 Technical Validation Passed.")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(validate_11_5())
