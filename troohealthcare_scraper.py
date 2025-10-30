import asyncio
import random
from playwright.async_api import async_playwright
from lxml import html

# Main category URLs
CATEGORY_URLS = [
    "https://www.troohealthcare.com/health-interests",
    "https://www.troohealthcare.com/supplements",
    "https://www.troohealthcare.com/pet-care",
    "https://www.troohealthcare.com/vitamins-minerals",
]

async def realistic_scroll(page, max_scrolls=100):
    """Scroll like a real user to load all infinite scroll products."""
    previous_count = 0
    same_count = 0
    max_same_count = 5

    for _ in range(max_scrolls):
        # Scroll a random small distance
        scroll_distance = random.randint(200, 400)
        await page.evaluate(f"window.scrollBy(0, {scroll_distance})")

        # Trigger wheel event to simulate user
        await page.mouse.wheel(0, scroll_distance)

        # Random delay to mimic human behavior
        await page.wait_for_timeout(random.randint(400, 800))

        # Count current products
        current_count = await page.evaluate(
            "document.querySelectorAll('.ajaxBusyPanelParent .product-title a').length"
        )

        loader_visible = await page.evaluate(
            "document.querySelector('.infinite-scroll-loader')?.style.display !== 'none'"
        )

        if current_count == previous_count:
            same_count += 1
        else:
            same_count = 0

        previous_count = current_count

        # Stop scrolling if loader hidden and no new products after a few iterations
        if same_count >= max_same_count and not loader_visible:
            break

async def get_h2_links(page):
    """Extract all h2 a links from category page."""
    content = await page.content()
    tree = html.fromstring(content)
    links = []
    for a in tree.cssselect("h2 a"):
        href = a.get("href")
        if href:
            if href.startswith("/"):
                href = "https://www.troohealthcare.com" + href
            elif not href.startswith("http"):
                href = "https://www.troohealthcare.com/" + href
            links.append((a.text_content().strip(), href))
    return links

async def get_product_links(page):
    """Scroll page fully and extract all product titles."""
    await realistic_scroll(page)
    content = await page.content()
    tree = html.fromstring(content)
    products = []
    for a in tree.cssselect(".ajaxBusyPanelParent .product-title a"):
        href = a.get("href")
        if href and not href.startswith("http"):
            href = "https://www.troohealthcare.com/" + href.lstrip("/")
        products.append((a.text_content().strip(), href))
    return products

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        all_products = []

        print("🌐 Fetching category pages...")
        for cat_url in CATEGORY_URLS:
            await page.goto(cat_url, wait_until="domcontentloaded")
            h2_links = await get_h2_links(page)
            print(f"✅ {cat_url}: {len(h2_links)} h2 links found")

            for title, link in h2_links:
                print(f"📦 Opening {title} ({link}) ...")
                try:
                    await page.goto(link, wait_until="domcontentloaded")
                    products = await get_product_links(page)
                    print(f"   → {len(products)} products")
                    all_products.extend(products)
                except Exception as e:
                    print(f"   ❌ Error fetching {link}: {e}")

        await browser.close()

        print("\n================= ALL PRODUCT LINKS =================")
        print(f"✅ Total products: {len(all_products)}")
        for name, link in all_products:
            print(f"- {name} → {link}")

if __name__ == "__main__":
    asyncio.run(main())
