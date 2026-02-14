from playwright.async_api import async_playwright
import asyncio

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        page.on("console", lambda msg: print(f"JS {msg.type.upper()}: {msg.text}"))
        page.on("pageerror", lambda err: print(f"JS ERROR: {err}"))
        
        await page.goto("http://localhost:8000")
        await asyncio.sleep(2)
        
        print("Clicking nav-admin...")
        await page.click("#nav-admin")
        await asyncio.sleep(1)
        
        admin_class = await page.get_attribute("#admin-panel", "class")
        print(f"Admin panel class: {admin_class}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
