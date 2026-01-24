import asyncio
from playwright.async_api import async_playwright

async def test_log_viewer():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        print("Navigating to A2UI...")
        await page.goto("http://localhost:8000")
        
        # Wait for page load
        await page.wait_for_selector("#the-stage")
        
        # Check if log viewer is hidden
        is_hidden = await page.eval_on_selector("#log-viewer", "el => el.classList.contains('hidden')")
        print(f"Log viewer initially hidden: {is_hidden}")
        
        # Trigger an error log via API
        print("Triggering system error log...")
        await page.request.get("http://localhost:8000/api/debug/error")
        
        # Log viewer should auto-show on error
        await page.wait_for_function("!document.getElementById('log-viewer').classList.contains('hidden')")
        print("Log viewer auto-showed on error.")
        
        # Check for error log content
        log_content = await page.inner_text("#log-content")
        print(f"Logs found: {log_content}")
        assert "CRITICAL_SYSTEM_FAILURE" in log_content
        
        # Check for color coding (log-error class)
        has_error_class = await page.eval_on_selector(".log-line.log-error", "el => el !== null")
        print(f"Log line has error class: {has_error_class}")
        assert has_error_class
        
        # Test Clear button
        print("Testing Clear button...")
        await page.click("#clear-logs")
        log_content_after_clear = await page.inner_text("#log-content")
        print(f"Logs after clear: '{log_content_after_clear}'")
        assert log_content_after_clear.strip() == ""
        
        # Test Toggle with 'L'
        print("Testing toggle with 'L' key...")
        await page.keyboard.press("l")
        is_hidden_after_l = await page.eval_on_selector("#log-viewer", "el => el.classList.contains('hidden')")
        print(f"Log viewer hidden after 'L': {is_hidden_after_l}")
        assert is_hidden_after_l
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_log_viewer())
