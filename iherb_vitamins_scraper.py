from playwright.sync_api import sync_playwright
import random
import time
import pandas as pd

# ==============================
# 🔧 CONFIGURATION
# ==============================

CATEGORY_URL = "https://www.iherb.com/c/vitamins"
CSV_FILE = "iherb_vitamins.csv"
PARQUET_FILE = "iherb_vitamins.parquet"

# User-Agents pool
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.200 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; rv:125.0) Gecko/20100101 Firefox/125.0",
]

# Ignore unnecessary tracking URLs
BLOCKED_URLS = ["v.clarity.ms", "fullstory.com", "nr-data.net", "googletagmanager.com"]

# Random restart interval (2–5 pages)
RESTART_INTERVAL = random.randint(2, 5)

# ==============================
# 🧠 HELPER FUNCTIONS
# ==============================

def get_random_user_agent():
    return random.choice(USER_AGENTS)

def human_delay(min_sec=1.5, max_sec=4.0):
    """Random small human-like delay."""
    time.sleep(random.uniform(min_sec, max_sec))

def block_unwanted_requests(route, request):
    """Block analytics/tracking requests."""
    if any(domain in request.url for domain in BLOCKED_URLS):
        route.abort()
    else:
        route.continue_()

def scroll_to_bottom(page):
    """Infinite scroll until page height stops increasing."""
    last_height = 0
    while True:
        page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
        time.sleep(random.uniform(1.0, 2.5))
        new_height = page.evaluate("document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

def extract_product_data(page):
    """Extract products from the current page."""
    products = []
    product_elements = page.locator(".product-inner").all()
    for el in product_elements:
        try:
            url_el = el.locator("a.absolute-link.product-link")
            product_url = url_el.get_attribute("href").strip() if url_el else ""
            title_el = el.locator(".product-title bdi")
            title = title_el.inner_text().strip() if title_el else ""
            img_el = el.locator(".product-image img")
            image_url = img_el.get_attribute("src").strip() if img_el else ""
            price_el = el.locator(".product-price .price bdi")
            price = price_el.inner_text().strip() if price_el else ""
            rating_el = el.locator(".stars.scroll-to")
            rating = rating_el.get_attribute("title").split("-")[0].strip() if rating_el else ""
            review_el = el.locator(".rating-count span")
            review_count = review_el.inner_text().strip() if review_el else ""
            sold_el = el.locator(".recent-activity-message-wrapper")
            sold_last_30_days = sold_el.inner_text().strip() if sold_el else ""

            products.append({
                "product_url": product_url,
                "title": title,
                "image_url": image_url,
                "price": price,
                "rating": rating,
                "review_count": review_count,
                "sold_last_30_days": sold_last_30_days
            })
        except Exception as e:
            print("❌ Parse error:", e)
            continue
    return products

# ==============================
# 🚀 MAIN SCRAPER
# ==============================

def scrape_iherb():
    global RESTART_INTERVAL
    all_data = []
    page_count = 0
    failed_attempts = 0
    current_page = 1

    while True:
        with sync_playwright() as p:
            user_agent = get_random_user_agent()
            print(f"\n🌐 Launching new browser session (UA: {user_agent[:40]}...)")
            browser = p.chromium.launch(
                headless=False,
                args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
            )
            context = browser.new_context(user_agent=user_agent)
            context.route("**/*", block_unwanted_requests)
            page = context.new_page()

            while True:
                print(f"\n🌐 Loading page {current_page} → {CATEGORY_URL}?p={current_page}")
                try:
                    page.goto(f"{CATEGORY_URL}?p={current_page}", timeout=60000, wait_until="domcontentloaded")
                    human_delay(2, 5)
                except Exception as e:
                    print(f"⚠️ Failed to load page {current_page}: {e}")
                    failed_attempts += 1
                    if failed_attempts > 3:
                        print("🔁 Too many failed attempts, restarting browser...")
                        break
                    continue

                failed_attempts = 0
                scroll_to_bottom(page)
                products = extract_product_data(page)
                if not products:
                    print(f"⚠️ No products found on page {current_page}")
                else:
                    all_data.extend(products)
                    print(f"🧾 Page scraped: {len(products)} products (Total: {len(all_data)})")
                    # Save to CSV & Parquet
                    df = pd.DataFrame(all_data)
                    df.to_csv(CSV_FILE, index=False)
                    try:
                        df.to_parquet(PARQUET_FILE, index=False)
                    except ImportError:
                        print("⚠️ Parquet not saved: install pyarrow or fastparquet")
                    print(f"💾 Data saved to {CSV_FILE}")

                # Next page logic
                next_button = page.locator('a.pagination-next')
                if next_button.is_visible():
                    try:
                        next_button.click()
                        human_delay(2, 5)
                        current_page += 1
                    except Exception:
                        print("⚠️ Could not click next button. Restarting browser...")
                        break
                else:
                    print("🚩 No more pages. Scraping complete.")
                    browser.close()
                    return

                # Restart browser every few pages
                if page_count % RESTART_INTERVAL == 0 and page_count > 0:
                    print(f"🔁 Restarting browser after {page_count} pages...")
                    browser.close()
                    RESTART_INTERVAL = random.randint(2, 5)
                    break

                page_count += 1

            browser.close()

# ==============================
# 🏁 ENTRY POINT
# ==============================

if __name__ == "__main__":
    scrape_iherb()
