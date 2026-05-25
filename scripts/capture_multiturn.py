"""Снимок одного многоходового диалога целиком — full-page после обоих ходов."""

import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "docs" / "theses_assets" / "screenshots"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = OUT_DIR / "03_clarification_multiturn.png"

BASE_URL = "http://localhost"


def login(page):
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=30_000)
    page.wait_for_timeout(2000)
    page.locator("input").nth(0).fill("admin", timeout=5000)
    page.locator("input[type='password']").first.fill("admin", timeout=5000)
    page.locator("button[type='submit']").first.click()
    page.wait_for_timeout(2500)


def fresh_chat(page):
    page.goto(BASE_URL + "/", wait_until="networkidle", timeout=15_000)
    page.wait_for_timeout(1500)


def clear_history(page):
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


def send_query(page, text: str, wait_ms: int):
    input_box = page.locator("textarea, input").last
    input_box.click()
    input_box.fill(text)
    input_box.press("Enter")
    page.wait_for_timeout(wait_ms)


def main():
    if OUT_PATH.exists():
        OUT_PATH.unlink()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        # Большой viewport — но снимок будет full_page, по реальной высоте контента
        ctx = browser.new_context(viewport={"width": 1440, "height": 1600}, locale="ru-RU")
        page = ctx.new_page()
        try:
            login(page)
            clear_history(page)
            fresh_chat(page)

            # Ход 1: указан только тип, цены нет → агент должен уточнить бюджет
            send_query(page, "Хочу электрогитару", wait_ms=12_000)
            # Ход 2: даём цену → у агента уже есть тип + бюджет → выдаёт результаты
            send_query(page, "до 700 долларов", wait_ms=20_000)

            # Прокручиваем чат в начало, чтобы первое сообщение было видно
            page.evaluate("""
            () => {
                const candidates = document.querySelectorAll('main, [role="log"], [class*="chat"], [class*="messages"]');
                for (const el of candidates) {
                    el.scrollTop = 0;
                }
                window.scrollTo(0, 0);
            }
            """)
            page.wait_for_timeout(800)

            page.screenshot(path=str(OUT_PATH), full_page=True)
            print(f"[ok] {OUT_PATH}", file=sys.stderr)
        except Exception as exc:
            print(f"[error] {exc}", file=sys.stderr)
            page.screenshot(path=str(OUT_DIR / "_error.png"))
        finally:
            browser.close()


if __name__ == "__main__":
    main()
