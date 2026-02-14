import pytest
from playwright.sync_api import Page, expect

# Mark all tests in this class as e2e
pytestmark = pytest.mark.e2e

class TestUiValidations:
    """
    Implementation of scenarios from docs/VALIDATIONS.md
    Requires a running server at http://localhost:8000
    """

    @pytest.fixture(autouse=True)
    def setup(self, page: Page):
        """Navigate to home page before each test"""
        # Fail test on console errors
        page.on("console", lambda msg: pytest.fail(f"JS Console Error: {msg.text}") if msg.type == "error" else None)
        # Fail test on network errors (404/500)
        page.on("requestfailed", lambda req: pytest.fail(f"Network Error: {req.url} failed") if req.url.startswith("http://localhost:8000") else None)

        try:
            page.goto("http://localhost:8000", timeout=5000)
            # Wait for basic hydration
            page.wait_for_load_state("networkidle")
        except Exception as e:
            pytest.fail(f"Could not connect to server: {e}. Ensure 'uvicorn apps.h-bridge.src.main:app' is running.")

    def test_background_presence(self, page: Page):
        """
        * [x] background : presence du background au chargement
        Verifier que le fond d'ecran de l'application est présent
        """
        bg = page.locator("#layer-bg")
        
        # 1. Element exists in DOM
        expect(bg).to_be_attached()
        
        # 2. Element is visible (not hidden)
        expect(bg).to_be_visible()
        
        # 3. Verify it has dimensions
        box = bg.bounding_box()
        assert box['width'] > 0
        assert box['height'] > 0
        
        # 4. Verify data-testid (from emergency fix)
        expect(bg).to_have_attribute("data-testid", "background")

    def test_avatar_presence(self, page: Page):
        """
        * [x] avatar : presence au chargement
        """
        avatar = page.locator("#avatar")
        
        # 1. Wrapper exists
        expect(avatar).to_be_attached()
        expect(avatar).to_be_visible()
        
        # 2. Check layers (body/face)
        body = page.locator("#layer-agent-body")
        face = page.locator("#layer-agent-face")
        
        expect(body).to_be_visible()
        expect(face).to_be_visible()
        
        # 3. Verify data-testid
        expect(avatar).to_have_attribute("data-testid", "avatar")

    def test_dashboard_interactions(self, page: Page):
        """
        * [x] dashboard : interactions
        """
        # Elements
        icon = page.locator("#nav-admin")
        panel = page.locator("#admin-panel")
        
        # Check icon presence via data-testid
        expect(icon).to_have_attribute("data-testid", "dashboard-icon")
        
        # 1. Click icon opens panel
        icon.click()
        expect(panel).to_be_visible()
        
        # 2. Click icon again closes panel
        icon.click()
        expect(panel).not_to_be_visible()
        
        # 3. Click outside closes panel
        icon.click() # Open again
        expect(panel).to_be_visible()
        
        # Click on background (0,0 is safe)
        page.mouse.click(10, 10)
        expect(panel).not_to_be_visible()
        
        # 4. Escape closes panel
        icon.click()
        expect(panel).to_be_visible()
        page.keyboard.press("Escape")
        expect(panel).not_to_be_visible()

    def test_crew_interactions(self, page: Page):
        """
        * [x] crew : interactions
        """
        icon = page.locator("#nav-crew")
        panel = page.locator("#crew-panel")
        
        expect(icon).to_have_attribute("data-testid", "crew-icon")
        
        # 1. Click icon opens panel
        icon.click()
        expect(panel).to_be_visible()
        
        # 2. Click icon again closes panel
        icon.click()
        expect(panel).not_to_be_visible()
        
        # 3. Click outside closes panel
        icon.click()
        expect(panel).to_be_visible()
        page.mouse.click(10, 10)
        expect(panel).not_to_be_visible()
        
        # 4. Escape closes panel
        icon.click()
        expect(panel).to_be_visible()
        page.keyboard.press("Escape")
        expect(panel).not_to_be_visible()
