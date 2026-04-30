#!/usr/bin/env python3
"""
用法: python3 bin/extract-body.py <url>
输出: markdown-body 的 outerHTML（stdout，已剥离 script/style，包成最小 HTML 文档）
"""
import sys
from playwright.sync_api import sync_playwright


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python3 extract-body.py <url>", file=sys.stderr)
        return 2
    url = sys.argv[1]

    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_context().new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            page.wait_for_selector("div.markdown-body", timeout=20_000)
            page.wait_for_function(
                "() => { const el = document.querySelector('div.markdown-body');"
                " return el && el.innerText && el.innerText.length > 50; }",
                timeout=10_000,
            )
            html = page.evaluate(
                """() => {
                    const mb = document.querySelector('div.markdown-body');
                    const clone = mb.cloneNode(true);
                    clone.querySelectorAll('script,style').forEach(n => n.remove());
                    return clone.outerHTML;
                }"""
            )
            sys.stdout.write(f"<!DOCTYPE html><html><body>{html}</body></html>")
            return 0
        finally:
            browser.close()


if __name__ == "__main__":
    sys.exit(main())
