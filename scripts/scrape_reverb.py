"""Скрапит реальные листинги с Reverb через Playwright и сохраняет в mock_reverb.json.

Запуск:
    source venv/bin/activate
    python3 scripts/scrape_reverb.py
"""

import json
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "tests" / "mock_reverb.json"

CATEGORIES = [
    ("/marketplace/electric-guitars", "electric", 15),
    ("/marketplace/acoustic-guitars", "acoustic", 10),
    ("/marketplace?query=classical+guitar", "classical", 15),
    ("/marketplace/bass-guitars", "bass", 10),
    ("/marketplace?query=stratocaster", "electric", 6),
    ("/marketplace?query=telecaster", "electric", 4),
    ("/marketplace?query=les+paul", "electric", 6),
    ("/marketplace?query=7+string+guitar", "electric", 4),
    # Бюджетный сегмент (sort by price ascending + price filter)
    ("/marketplace/electric-guitars?price_max=700&sort=price-asc", "electric", 15),
    ("/marketplace/acoustic-guitars?price_max=600&sort=price-asc", "acoustic", 15),
    ("/marketplace/bass-guitars?price_max=600&sort=price-asc", "bass", 10),
    ("/marketplace?query=telecaster&price_max=800&sort=price-asc", "electric", 10),
    ("/marketplace?query=stratocaster&price_max=800&sort=price-asc", "electric", 10),
    ("/marketplace?query=les+paul&price_max=1000&sort=price-asc", "electric", 10),
    ("/marketplace?query=squier&price_max=600&sort=price-asc", "electric", 8),
    ("/marketplace?query=epiphone&price_max=800&sort=price-asc", "electric", 8),
]

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
)


def parse_price(text):
    if not text:
        return None
    m = re.search(r"([\d,]+(?:\.\d+)?)", text)
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", ""))
    except ValueError:
        return None


def parse_year(title):
    m = re.search(r"\b(19[5-9]\d|20[0-3]\d)\b", title or "")
    return int(m.group(1)) if m else None


def normalize_condition(text):
    if not text:
        return "used"
    t = text.lower()
    for key in ("mint", "excellent", "very good", "good", "fair", "poor", "brand new", "new"):
        if key in t:
            return "mint" if key == "brand new" else key
    return "used"


def scrape_category(page, path, kind, want):
    url = f"https://reverb.com{path}"
    print(f"[scrape] → {url}", file=sys.stderr)
    page.goto(url, wait_until="domcontentloaded", timeout=60_000)
    try:
        page.wait_for_selector(".rc-listing-card", timeout=30_000)
    except PWTimeout:
        print(f"[scrape] no cards on {path}", file=sys.stderr)
        return []
    # Lazy-scroll
    for _ in range(5):
        page.mouse.wheel(0, 4000)
        time.sleep(0.7)

    cards = page.evaluate(
        """
        () => {
            const out = [];
            const seen = new Set();
            for (const card of document.querySelectorAll(".rc-listing-card")) {
                const a = card.querySelector("a.rc-listing-card__title-element, a[href*='/item/']");
                if (!a) continue;
                const href = a.href.split('?')[0];
                if (seen.has(href)) continue;
                const title = (a.getAttribute('aria-label') || a.innerText || '').trim().split('\\n')[0].trim();
                if (!title) continue;
                const priceEl = card.querySelector(".rc-listing-card__price");
                const price = priceEl ? priceEl.innerText.trim() : null;
                const condEl = card.querySelector(".rc-listing-card__condition");
                const condition = condEl ? condEl.innerText.trim() : null;
                const img = card.querySelector(".rc-listing-card__thumbnail img, img");
                let imgUrl = null;
                if (img) {
                    imgUrl = img.getAttribute('src') || img.getAttribute('data-src');
                    if (!imgUrl) {
                        const srcset = img.getAttribute('srcset');
                        if (srcset) imgUrl = srcset.split(',')[0].trim().split(' ')[0];
                    }
                }
                seen.add(href);
                out.push({ href, title, price, condition, image_url: imgUrl });
            }
            return out;
        }
        """
    )

    items = []
    for idx, c in enumerate(cards):
        if len(items) >= want:
            break
        price = parse_price(c.get("price") or "")
        if price is None or price <= 0:
            continue
        listing_url = c["href"]
        id_match = re.search(r"/item/(\d+)", listing_url)
        item_id = f"rev_{id_match.group(1)}" if id_match else f"rev_{kind}_{idx}"
        items.append({
            "id": item_id,
            "title": c["title"],
            "price": price,
            "currency": "USD",
            "image_url": c.get("image_url") or "",
            "listing_url": listing_url,
            "year": parse_year(c["title"]),
            "condition": normalize_condition(c.get("condition")),
            "category": kind,
        })
    print(f"[scrape] {kind}: {len(items)} items", file=sys.stderr)
    return items


def main():
    all_items = []
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": 1440, "height": 900},
            locale="en-US",
        )
        context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        )
        page = context.new_page()
        for path, kind, want in CATEGORIES:
            try:
                all_items.extend(scrape_category(page, path, kind, want))
            except Exception as exc:
                print(f"[scrape] failed {path}: {exc}", file=sys.stderr)
        browser.close()

    # Dedup by id (same item can appear in multiple queries)
    seen = set()
    deduped = []
    for it in all_items:
        if it["id"] in seen:
            continue
        seen.add(it["id"])
        deduped.append(it)
    print(f"[scrape] deduped: {len(all_items)} → {len(deduped)}", file=sys.stderr)
    all_items = deduped

    if not all_items:
        print("[scrape] no items collected", file=sys.stderr)
        sys.exit(1)

    print(f"[scrape] total: {len(all_items)} items → {OUTPUT}", file=sys.stderr)
    OUTPUT.write_text(json.dumps(all_items, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
