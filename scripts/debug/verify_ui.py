from playwright.sync_api import sync_playwright
import sys
import time

def run():
    print("Starting Playwright check...")
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
        except Exception as e:
            print(f"Failed to launch browser: {e}")
            return

        page = browser.new_page()
        page.on("console", lambda msg: print(f"BROWSER_LOG: {msg.text}"))
        print("Navigating to http://192.168.200.61:8000 ...")
        try:
            page.goto("http://192.168.200.61:8000", timeout=10000)
        except Exception as e:
            print(f"Navigation failed: {e}")
            browser.close()
            sys.exit(1)
        
        print("Waiting for rendering logic...")
        # Wait for the background to have a style attribute with 'url'
        try:
            page.wait_for_function("document.getElementById('layer-bg').style.backgroundImage.includes('url')", timeout=5000)
            print("Background loaded.")
        except Exception as e:
            print(f"Timeout waiting for background: {e}")

        # Check background
        bg = page.locator("#layer-bg")
        bg_style = bg.get_attribute("style")
        print(f"Background Style: {bg_style}")
        
        # Check body
        body = page.locator("#layer-agent-body")
        body_style = body.get_attribute("style")
        print(f"Body Style: {body_style}")
        
        # Screenshot
        try:
            page.screenshot(path="ui_verify.png")
            print("Screenshot saved to ui_verify.png")
        except Exception as e:
            print(f"Screenshot failed: {e}")
        
        if bg_style and "url" in bg_style:
            if body_style and "url" in body_style:
                print("SUCCESS: Background and Avatar detected.")
            else:
                print("PARTIAL: Background detected, but Avatar missing.")
        else:
            print("FAILURE: Missing visual elements.")
            
        browser.close()

if __name__ == "__main__":
    run()
