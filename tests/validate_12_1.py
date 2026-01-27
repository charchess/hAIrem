from playwright.sync_api import sync_playwright
import time
import re

def validate_speech_queue():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) # Set to False if you want to see it
        page = browser.new_page()
        
        # Enable console logging
        page.on("console", lambda msg: print(f"BROWSER: {msg.text}"))
        page.on("pageerror", lambda err: print(f"BROWSER ERROR: {err}"))
        
        print("Loading A2UI...")
        try:
            page.goto("http://localhost:8080")
        except Exception as e:
            print(f"Error loading page: {e}. Is the server running?")
            return

        # Wait for initialization
        try:
            page.wait_for_selector("#agent-name", state="visible", timeout=5000)
        except:
            print("Timeout waiting for UI. Check if H-Core is running.")
            return

        print("\n--- Test 1: Sequential Display ---")
        # Inject simulated messages via console
        print("Injecting simultaneous messages...")
        page.evaluate("""
            const msg1 = {
                type: \"narrative.text\",
                sender: { agent_id: \"AgentA\", role: \"test\" },
                payload: { content: \"Message One [pose:happy]\" }
            };
            const msg2 = {
                type: \"narrative.text\",
                sender: { agent_id: \"AgentB\", role: \"test\" },
                payload: { content: \"Message Two [pose:neutral]\" }
            };
            if (window.network) {
                window.network.handleMessage(msg1);
                window.network.handleMessage(msg2);
            } else {
                console.error(\"Network client not found!\");
            }
        """)

        # 1. Check first message is displayed immediately
        print("Verifying Message One...")
        try:
            # Short wait for React/DOM update
            page.wait_for_timeout(500)
            # Handle CSS uppercase transform
            current_name = page.locator("#agent-name").inner_text()
            assert current_name.upper() == "AGENTA"
            print("PASS: Message One visible.")
        except AssertionError as e:
            print(f"FAIL: Message One not visible correctly. Found name: '{page.locator('#agent-name').inner_text()}'")

        # 2. Verify AgentB hasn't started yet (Queueing)
        print("Verifying Message Two is queued...")
        page.wait_for_timeout(500) 
        try:
            current_name = page.locator("#agent-name").inner_text()
            assert current_name.upper() == "AGENTA"
            print("PASS: Still showing AgentA (Queue active).")
        except AssertionError:
            print(f"FAIL: Queue failed, AgentB appeared too early. Found name: '{page.locator('#agent-name').inner_text()}'")

        # 3. Wait for transition
        print("Waiting for queue transition (~2.5s)...")
        page.wait_for_timeout(2500)

        # 4. Check second message is now displayed
        print("Verifying Message Two...")
        try:
            current_name = page.locator("#agent-name").inner_text()
            assert current_name.upper() == "AGENTB"
            print("PASS: Message Two visible.")
        except AssertionError:
            print(f"FAIL: Message Two did not appear. Found name: '{page.locator('#agent-name').inner_text()}'")


        print("\n--- Test 2: Active Speaker Dashboard ---")
        # Clear queue from previous test
        page.evaluate("if(window.speechQueue) window.speechQueue.clear()")
        
        # Switch to Dashboard
        page.locator("#nav-dashboard").click()
        page.wait_for_selector("#agent-dashboard", state="visible")

        # Inject Agent Metadata to ensure cards exist
        page.evaluate("""
            if (window.renderer) {
                window.renderer.updateAgentCards([
                    { id: \"AgentA\", commands: [], status: \"idle\", mood: \"neutral\" },
                    { id: \"AgentB\", commands: [], status: \"idle\", mood: \"neutral\" }
                ]);
            }
        """)

        # Inject message to trigger active speaker
        print("Injecting message for AgentA...")
        page.evaluate("""
            window.network.handleMessage({
                type: \"narrative.text\",
                sender: { agent_id: \"AgentA\" },
                payload: { content: \"Speaking now.\" }
            });
        """)

        # Check for active class
        print("Checking AgentA highlight...")
        # Give a moment for the event to process
        page.wait_for_timeout(200)
        
        agent_a_card = page.locator(".agent-card", has_text="AgentA")
        try:
            # Check class list manually since we are using sync api simply
            classes = agent_a_card.get_attribute("class")
            assert "active-speaker" in classes
            print("PASS: AgentA has active-speaker class.")
        except AssertionError:
             print(f"FAIL: AgentA missing active-speaker class. Found: {agent_a_card.get_attribute('class')}")

        # Wait for finish
        print("Waiting for speech to finish...")
        page.wait_for_timeout(3000) # > 2000ms min duration

        # Check highlight removed
        print("Checking AgentA highlight removed...")
        try:
            classes = agent_a_card.get_attribute("class")
            assert "active-speaker" not in classes
            print("PASS: Active speaker class removed.")
        except AssertionError:
            print(f"FAIL: AgentA still has active-speaker class. Found: {classes}")

        browser.close()

if __name__ == "__main__":
    validate_speech_queue()