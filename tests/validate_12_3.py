from playwright.sync_api import sync_playwright
import time

def validate_dashboard_fixes():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Enable console logging
        page.on("console", lambda msg: print(f"BROWSER: {msg.text}"))
        
        print("Loading A2UI...")
        try:
            page.goto("http://localhost:8080")
        except Exception as e:
            print(f"Error loading page: {e}. Is the server running?")
            return

        # Wait for initialization
        try:
            page.wait_for_selector("#nav-dashboard", state="visible", timeout=5000)
        except:
            print("Timeout waiting for UI.")
            return

        print("\n--- Test 1: Dashboard Navigation & Close Button ---")
        # 1. Open Dashboard
        page.locator("#nav-dashboard").click()
        page.wait_for_selector("#agent-dashboard", state="visible")
        
        # 2. Verify Close Button Works
        close_btn = page.locator("#close-dashboard")
        assert close_btn.is_visible(), "Close button should be visible"
        close_btn.click()
        
        # 3. Verify Dashboard is hidden
        page.wait_for_selector("#agent-dashboard", state="hidden")
        print("PASS: Dashboard closed via 'X' button.")


        print("\n--- Test 2: Agent Activation Toggle ---")
        # Re-open Dashboard
        page.locator("#nav-dashboard").click()
        page.wait_for_selector("#agent-dashboard", state="visible")
        
        # Inject Mock Agent Data
        page.evaluate("""
            window.renderer.updateAgentCards([
                { id: \"AgentTest\", commands: [], active: true, status: \"idle\", mood: \"neutral\" }
            ]);
        """)
        
        # Locate the card and toggle
        card = page.locator(".agent-card", has_text="AgentTest")
        toggle_input = card.locator("input[type='checkbox']")
        toggle_slider = card.locator(".slider")
        
        assert toggle_input.is_checked(), "Toggle should be checked initially"
        assert "disabled" not in card.get_attribute("class"), "Card should not be disabled"
        
        # Click toggle to disable (Click the visual slider)
        print("Disabling AgentTest...")
        toggle_slider.click()
        
        # Verify visual state
        page.wait_for_timeout(100)
        assert not toggle_input.is_checked(), "Toggle should be unchecked"
        assert "disabled" in card.get_attribute("class"), "Card should have 'disabled' class"
        print("PASS: Visual feedback for disabled agent verified.")
        
        # Click toggle to enable
        print("Enabling AgentTest...")
        toggle_slider.click()
        
        page.wait_for_timeout(100)
        assert toggle_input.is_checked(), "Toggle should be checked"
        assert "disabled" not in card.get_attribute("class"), "Card should be enabled"
        print("PASS: Re-enabling verified.")

        browser.close()

if __name__ == "__main__":
    validate_dashboard_fixes()
