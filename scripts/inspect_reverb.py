"""Открывает Reverb и сохраняет HTML + структуру первой карточки для дебага."""

import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path("/tmp/reverb-inspect.html")
STRUCT = Path("/tmp/reverb-struct.txt")

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
        context = browser.new_context(user_agent=USER_AGENT, viewport={"width": 1440, "height": 900})
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined});")
        page = context.new_page()
        page.goto("https://reverb.com/marketplace/electric-guitars", wait_until="domcontentloaded", timeout=60_000)
        try:
            page.wait_for_selector("a[href*='/item/']", timeout=30_000)
        except Exception:
            print("no /item/ links — full page block", file=sys.stderr)
        page.mouse.wheel(0, 1500)
        page.wait_for_timeout(2000)

        html = page.content()
        OUT.write_text(html)
        print(f"saved html: {len(html)} bytes → {OUT}", file=sys.stderr)

        info = page.evaluate("""
        () => {
            const a = document.querySelector("a[href*='/item/']");
            if (!a) return { found: false };
            const ancestors = [];
            let el = a;
            for (let i = 0; i < 10 && el; i++) {
                ancestors.push({
                    tag: el.tagName,
                    cls: el.className?.toString?.() || '',
                    data: Object.keys(el.dataset || {}).join(','),
                    id: el.id || '',
                });
                el = el.parentElement;
            }
            return { found: true, href: a.href, title: a.getAttribute('aria-label') || a.innerText?.slice(0,100), ancestors };
        }
        """)
        STRUCT.write_text(str(info))
        print(f"struct → {STRUCT}", file=sys.stderr)
        print(info, file=sys.stderr)

        browser.close()


if __name__ == "__main__":
    main()
