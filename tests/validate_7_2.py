import asyncio
from playwright.async_api import async_playwright
import httpx
import time

async def validate_system_logs():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("Navigating to http://localhost:8000 ...")
        await page.goto("http://localhost:8000")
        
        # 1. Verify Log Viewer can be toggled
        print("Testing log viewer toggle (shortcut 'L')...")
        log_viewer = page.locator("#log-viewer")
        await page.keyboard.press("l")
        await log_viewer.wait_for(state="visible")
        assert await log_viewer.is_visible(), "Log viewer should be visible after pressing 'L'"
        
        # 2. Trigger a debug error log
        print("Waiting for WebSocket to settle...")
        await asyncio.sleep(2)
        print("Triggering debug error via API...")
        async with httpx.AsyncClient() as client:
            resp = await client.get("http://localhost:8000/api/debug/error")
            assert resp.status_code == 200
        
        # 3. Check if log entry appeared in the viewer
        print("Waiting for error log to appear in UI...")
        log_content = page.locator("#log-content")
        # Wait for a log line with 'log-error' class
        error_line = log_content.locator(".log-error")
        await error_line.wait_for(state="visible", timeout=5000)
        
        text = await error_line.inner_text()
        print(f"Detected log: {text}")
        assert "CRITICAL_SYSTEM_FAILURE" in text, "Error log message not found in viewer"
        
        # 4. Verify auto-show on error
        print("Testing auto-show on error...")
        # Hide it first
        await page.keyboard.press("l")
        await log_viewer.wait_for(state="hidden")
        
        # Trigger another error
        async with httpx.AsyncClient() as client:
            await client.get("http://localhost:8000/api/debug/error")
            
        # Should auto-show
        await log_viewer.wait_for(state="visible", timeout=5000)
        print("Log viewer auto-showed on error.")

        # 5. Test Clear button
        print("Testing Clear button...")
        clear_btn = page.locator("#clear-logs")
        await clear_btn.click()
        lines_count = await log_content.locator(".log-line").count()
        assert lines_count == 0, "Logs should be cleared"
        print("Clear button verified.")

        print("All system log validations passed!")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(validate_system_logs())
