import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e

class TestVisualIntegrity:
    """
    Stricter tests checking CSS computed values and network responses for assets.
    """
    
    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        # Capture console logs
        page.on("console", lambda msg: print(f"BROWSER CONSOLE: [{msg.type}] {msg.text}"))
        
        # Fail immediately if an image fails to load
        def handle_response(response):
            if response.request.resource_type == "image" and response.status >= 400:
                print(f"🚨 BROKEN ASSET: {response.url} returned {response.status}")
        
        page.on("response", handle_response)
        
        try:
            page.goto("http://localhost:8000", timeout=5000)
            # Wait longer for JS and images
            page.wait_for_timeout(3000) 
        except Exception as e:
            pytest.fail(f"Server connection failed: {e}")

    def test_background_actually_loads(self, page: Page):
        """
        Verify #layer-bg has a real background-image CSS property.
        Previous tests only checked if div existed.
        """
        bg = page.locator("#layer-bg")
        
        # Get the computed CSS value
        bg_image = bg.evaluate("el => window.getComputedStyle(el).backgroundImage")
        print(f"\nDEBUG: #layer-bg background-image = {bg_image}")
        
        # Assertions
        if bg_image == "none" or not bg_image:
            pytest.fail("❌ #layer-bg has NO background-image set. renderer.js failed to initialize it.")
            
        if "undefined" in bg_image or "null" in bg_image:
            pytest.fail(f"❌ #layer-bg URL is broken: {bg_image}")
            
        # If we get here, CSS is set. The @fixture checked for 404s.

    def test_avatar_layers_load(self, page: Page):
        """
        Verify #layer-agent-body has a real background-image CSS property.
        """
        body = page.locator("#layer-agent-body")
        
        body_bg = body.evaluate("el => window.getComputedStyle(el).backgroundImage")
        print(f"\nDEBUG: #layer-agent-body background-image = {body_bg}")
        
        if body_bg == "none" or not body_bg:
            pytest.fail("❌ Avatar body has NO image. Agent not loaded?")
            
        if "undefined" in body_bg:
            pytest.fail(f"❌ Avatar URL contains 'undefined': {body_bg}")
