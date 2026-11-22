import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page(viewport={'width':1080,'height':1080})
        await pg.goto('file:///home/claude/main/brand/coogle/pfp.html'); await pg.wait_for_timeout(500)
        for k in 'ABC':
            await pg.locator('#'+k).screenshot(path=f'pfp_{k}.png')
        await b.close()
asyncio.run(main())
