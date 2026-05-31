#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性：把 GA4 (gtag.js) 追蹤碼插入全站每頁 <head>（冪等、可重複執行）。
排除 embed/（嵌入式 widget，CSP 不允許外部腳本且不應追蹤第三方訪客）。"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GA_ID = "G-5WQV8QQDBJ"

SNIPPET = (
    "\n  <!-- Google tag (gtag.js) -->\n"
    f'  <script async src="https://www.googletagmanager.com/gtag/js?id={GA_ID}"></script>\n'
    "  <script>\n"
    "    window.dataLayer = window.dataLayer || [];\n"
    "    function gtag(){dataLayer.push(arguments);}\n"
    "    gtag('js', new Date());\n"
    f"    gtag('config', '{GA_ID}');\n"
    "  </script>"
)

inserted, skipped, no_head = 0, 0, []
for dirpath, dirnames, filenames in os.walk(ROOT):
    if os.sep + "embed" in dirpath or os.sep + "node_modules" in dirpath or os.sep + ".git" in dirpath:
        continue
    for fn in filenames:
        if not fn.endswith(".html"):
            continue
        path = os.path.join(dirpath, fn)
        with open(path, encoding="utf-8") as f:
            html = f.read()
        if GA_ID in html or "googletagmanager.com/gtag" in html:
            skipped += 1
            continue
        m = re.search(r"<head[^>]*>", html, re.IGNORECASE)
        if not m:
            no_head.append(os.path.relpath(path, ROOT))
            continue
        idx = m.end()
        html = html[:idx] + SNIPPET + html[idx:]
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        inserted += 1

print(f"插入 {inserted} 頁、已存在略過 {skipped} 頁。")
if no_head:
    print("找不到 <head> 的檔案：", no_head)
