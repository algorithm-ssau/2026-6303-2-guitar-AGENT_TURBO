"""Открывает UI и дампит структуру для скриншот-скрипта."""
import sys
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_context(viewport={"width": 1440, "height": 900}).new_page()
    page.goto("http://localhost", wait_until="networkidle", timeout=30_000)
    page.wait_for_timeout(2000)
    # Дамп всех видимых input + button + ссылок
    info = page.evaluate("""
    () => {
        const out = {inputs: [], buttons: [], links: [], h: location.href};
        document.querySelectorAll('input').forEach(el => out.inputs.push({
            type: el.type, name: el.name, placeholder: el.placeholder, id: el.id
        }));
        document.querySelectorAll('button').forEach(el => out.buttons.push({
            text: (el.innerText||'').slice(0,40), type: el.type
        }));
        document.querySelectorAll('a').forEach(el => out.links.push({
            text: (el.innerText||'').slice(0,40), href: el.getAttribute('href')
        }));
        return out;
    }
    """)
    print("URL:", info['h'], file=sys.stderr)
    print("INPUTS:", file=sys.stderr)
    for i in info['inputs']: print(" ", i, file=sys.stderr)
    print("BUTTONS:", file=sys.stderr)
    for b in info['buttons']: print(" ", b, file=sys.stderr)
    print("LINKS:", file=sys.stderr)
    for l in info['links'][:10]: print(" ", l, file=sys.stderr)
    page.screenshot(path="/tmp/ui-inspect.png")
    print("screenshot /tmp/ui-inspect.png", file=sys.stderr)
    browser.close()
