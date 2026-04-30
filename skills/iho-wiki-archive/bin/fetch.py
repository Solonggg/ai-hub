#!/usr/bin/env python3
"""
用法: python3 bin/fetch.py <url>
输出: 渲染后整页 HTML（stdout）
退出码: 0 成功 / 2 参数错误 / 3 加载失败 / 4 markdown-body 为空
"""
import sys
from playwright.sync_api import sync_playwright


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python3 fetch.py <url>", file=sys.stderr)
        return 2
    url = sys.argv[1]

    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_context().new_page()
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30_000)
                page.wait_for_selector("div.markdown-body", timeout=20_000)
                page.wait_for_function(
                    "() => { const el = document.querySelector('div.markdown-body');"
                    " return el && el.innerText && el.innerText.length > 50; }",
                    timeout=10_000,
                )
            except Exception as e:
                print(f"[fetch.py] load/wait failed: {e}", file=sys.stderr)
                return 3

            empty = page.evaluate(
                "() => { const el = document.querySelector('div.markdown-body');"
                " return !el || !el.innerText || el.innerText.length < 50; }"
            )
            if empty:
                print("[fetch.py] markdown-body empty after wait", file=sys.stderr)
                return 4

            sys.stdout.write(page.content())
            return 0
        finally:
            browser.close()


if __name__ == "__main__":
    sys.exit(main())
