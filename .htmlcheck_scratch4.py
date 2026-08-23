import re

files = [
 "articles/00961-vs-00929-vs-00934.html",
 "articles/china-ai-token-futures-impact.html",
 "articles/fubon-tech-0052-dividend.html",
 "articles/health-insurance-dividend.html",
 "articles/stock-saving-outlook-h2-2026.html",
 "articles/tsmc-revenue-record-2026.html",
 "articles/taiwan-stock-market-june-2026.html",
]

for f in files:
    c = open(f, encoding='utf-8').read()
    m = re.search(r'<h1[^>]*>(.*?)</h1>(.*?)<p[^>]*>(.*?)</p>', c, re.S)
    print("===", f, "===")
    if m:
        h1 = re.sub(r'<[^>]+>', '', m.group(1)).strip()
        p = re.sub(r'<[^>]+>', '', m.group(3)).strip()[:150]
        print("H1:", h1)
        print("P1:", p)
    print()
