"""Скриншоты UI через Playwright. Каждый сценарий — отдельный чистый контекст."""

import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "docs" / "theses_assets" / "screenshots"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "http://localhost"


def login(page):
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30_000)
    page.wait_for_timeout(2000)
    page.locator("input").nth(0).fill("admin", timeout=5000)
    page.locator("input[type='password']").first.fill("admin", timeout=5000)
    page.locator("button[type='submit']").first.click()
    page.wait_for_timeout(2500)


def fresh_chat(page):
    """Гарантированно переходит в новый пустой чат через URL."""
    page.goto(BASE_URL + "/", wait_until="networkidle", timeout=15_000)
    page.wait_for_timeout(1500)


def clear_history(page):
    """Чистит sidebar — удаляет сессии через API."""
    # Берём auth token из localStorage и дёргаем DELETE /api/history напрямую
    result = page.evaluate("""
    async () => {
        const token = localStorage.getItem('guitar-agent-token');
        if (!token) return 'no token';
        const r = await fetch('/api/history', {
            method: 'DELETE',
            headers: { 'Authorization': 'Bearer ' + token }
        });
        return r.status;
    }
    """)
    print(f"[ok] clear /api/history → {result}", file=sys.stderr)
    page.wait_for_timeout(1500)
    page.reload()
    page.wait_for_timeout(2000)


def send_query(page, text: str, wait_ms: int = 15_000):
    input_box = page.locator("textarea, input").last
    input_box.click()
    input_box.fill(text)
    input_box.press("Enter")
    page.wait_for_timeout(wait_ms)


def shot(page, name: str):
    path = OUT_DIR / f"{name}.png"
    page.screenshot(path=str(path), full_page=False)
    print(f"[ok] {path}", file=sys.stderr)


def main():
    # Чистим
    for f in OUT_DIR.glob("*.png"):
        f.unlink()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--disable-blink-features=AutomationControlled"])
        # Большая высота — короткие диалоги влезают целиком
        ctx = browser.new_context(viewport={"width": 1280, "height": 1100}, locale="ru-RU")
        page = ctx.new_page()
        try:
            login(page)
            # Очищаем sidebar от мусора перед прогоном
            clear_history(page)

            # 1. Пустой чат — welcome
            fresh_chat(page)
            shot(page, "01_chat_empty")

            # 2. Основной поиск
            fresh_chat(page)
            send_query(page, "Хочу телекастер с ярким звуком, до $800", wait_ms=15_000)
            shot(page, "02_search_telecaster")

            # 3. Multi-turn clarification — 2 кадра
            fresh_chat(page)
            send_query(page, "Хочу гитару", wait_ms=10_000)
            shot(page, "03a_clarification_question")
            send_query(page, "до 700 долларов", wait_ms=12_000)
            shot(page, "03b_clarification_resolved")

            # 4. Empty + action button
            fresh_chat(page)
            send_query(page, "Хочу гитару за $50", wait_ms=12_000)
            shot(page, "04_empty_with_actions")

            # 5. Консультация
            fresh_chat(page)
            send_query(page, "Чем отличается P90 от хамбакера?", wait_ms=20_000)
            shot(page, "05_consultation_p90")
        except Exception as exc:
            print(f"[error] {exc}", file=sys.stderr)
            page.screenshot(path=str(OUT_DIR / "_error.png"))
        finally:
            input("Enter для закрытия...")
            browser.close()


if __name__ == "__main__":
    main()
