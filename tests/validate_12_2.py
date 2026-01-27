from playwright.sync_api import sync_playwright
import time

def validate_ui_feedback():
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
            page.wait_for_selector("#status-ws", state="visible", timeout=5000)
        except:
            print("Timeout waiting for Status Indicators.")
            return

        print("\n--- Test 1: Health Indicators ---")
        # Check initial state (should be OK if server runs)
        # Note: If server just started, it might take up to 30s for the health loop to fire.
        # But WS status is handled by network.js on connect.
        
        print("Checking WebSocket Status Indicator...")
        # Should be 'ok' or 'checking' -> 'ok'
        page.wait_for_timeout(1000) 
        ws_status = page.locator("#status-ws")
        expect_class(ws_status, "ok")

        print("Checking System Health Updates...")
        # Simulate a system status update from backend
        page.evaluate("""
            window.network.handleMessage({
                type: \"system.status_update\",
                sender: { agent_id: \"core\" },
                recipient: { target: \"system\" },
                payload: { content: { component: \"redis\", status: \"ok\" } }
            });
        """)
        page.wait_for_timeout(200)
        expect_class(page.locator("#status-redis"), "ok")

        print("Simulating LLM Failure...")
        page.evaluate("""
            window.network.handleMessage({
                type: \"system.status_update\",
                sender: { agent_id: \"core\" },
                recipient: { target: \"system\" },
                payload: { content: { component: \"llm\", status: \"error\" } }
            });
        """)
        page.wait_for_timeout(200)
        expect_class(page.locator("#status-llm"), "error")


        print("\n--- Test 2: Input Lockdown ---")
        # Simulate WS Disconnect (Error state)
        print("Simulating WS Error...")
        page.evaluate("""
            window.renderer.updateSystemStatus('ws', 'error');
        """)
        page.wait_for_timeout(200)
        
        # Input should be disabled
        is_disabled = page.locator("#chat-input").is_disabled()
        print(f"Input Disabled: {is_disabled}")
        assert is_disabled, "Chat input should be disabled when WS is down"

        # Simulate WS Recovery
        print("Simulating WS Recovery...")
        page.evaluate("""
            window.renderer.updateSystemStatus('ws', 'ok');
        """)
        page.wait_for_timeout(200)
        is_disabled = page.locator("#chat-input").is_disabled()
        print(f"Input Disabled: {is_disabled}")
        assert not is_disabled, "Chat input should be enabled when WS is ok"


        print("\n--- Test 3: Send Button Loading State ---")
        # Click send and check for loading class
        # Note: We need to mock the send function or just call setProcessingState manually 
        # because the real send clears the input too fast.
        
        print("Manually triggering processing state...")
        page.evaluate("window.renderer.setProcessingState(true)")
        page.wait_for_timeout(100)
        
        send_btn = page.locator("#chat-send")
        classes = send_btn.get_attribute("class")
        print(f"Send Button Classes: {classes}")
        assert "loading" in classes, "Send button should have loading class"
        assert send_btn.inner_text() == "...", "Send button text should be '...'"
        
        page.evaluate("window.renderer.setProcessingState(false)")
        page.wait_for_timeout(100)
        classes = send_btn.get_attribute("class")
        assert "loading" not in classes, "Send button should NOT have loading class"
        # Handle CSS text-transform: uppercase
        assert send_btn.inner_text().upper() == "ENVOYER"

        browser.close()

def expect_class(locator, class_name):
    classes = locator.get_attribute("class")
    if class_name in classes:
        print(f"PASS: {locator} has class '{class_name}'")
    else:
        print(f"FAIL: {locator} missing class '{class_name}'. Found: '{classes}'")
        raise AssertionError(f"Missing class {class_name}")

if __name__ == "__main__":
    validate_ui_feedback()
