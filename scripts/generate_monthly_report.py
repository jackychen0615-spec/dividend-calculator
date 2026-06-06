#!/usr/bin/env python3
"""
每月自動生成台股月報文章
- 抓 TWSE 大盤資料（月漲跌、成交量）
- 抓熱門 ETF 殖利率
- 生成 HTML 文章
- 更新 sitemap
"""

import json
import urllib.request
import datetime
import os
import re
import ssl

SITE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTICLES_DIR = os.path.join(SITE_DIR, 'articles')
SITEMAP_PATH = os.path.join(SITE_DIR, 'sitemap.xml')

# 台灣月份名稱
MONTH_NAMES = {1:'一月',2:'二月',3:'三月',4:'四月',5:'五月',6:'六月',
               7:'七月',8:'八月',9:'九月',10:'十月',11:'十一月',12:'十二月'}

def fetch_json(url):
    """Fetch JSON from URL"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'})
    try:
        resp = urllib.request.urlopen(req, timeout=15, context=ctx)
        return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def get_market_data():
    """Get market index data from TWSE"""
    # 大盤指數
    data = fetch_json('https://openapi.twse.com.tw/v1/exchangeReport/MI_INDEX')
    taiex = None
    if data:
        for item in data:
            if '加權' in str(item.get('指數', '')):
                taiex = item
                break
    return taiex

def get_top_etf_yields():
    """Get top ETF yields from BWIBBU_ALL"""
    data = fetch_json('https://openapi.twse.com.tw/v1/exchangeReport/BWIBBU_ALL')
    if not data:
        return []

    target_codes = ['0050','0056','00713','00878','00919','00929','00940','006208']
    etfs = []
    for item in data:
        if item.get('Code') in target_codes:
            etfs.append({
                'code': item['Code'],
                'name': item.get('Name','').strip(),
                'yield': item.get('DividendYield','0'),
                'pe': item.get('PEratio','N/A')
            })
    return etfs

def get_stock_prices():
    """Get closing prices for key stocks"""
    data = fetch_json('https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL')
    if not data:
        return {}

    targets = ['0050','0056','00878','00919','00929','00940','2330','2886','2891']
    prices = {}
    for item in data:
        if item.get('Code') in targets:
            prices[item['Code']] = {
                'name': item.get('Name','').strip(),
                'price': item.get('ClosingPrice','0'),
                'change': item.get('Change','0'),
                'volume': item.get('TradeVolume','0')
            }
    return prices

def generate_article(now, etfs, prices):
    """Generate the monthly report HTML"""
    year = now.year
    month = now.month
    # Report is for previous month
    if month == 1:
        report_month = 12
        report_year = year - 1
    else:
        report_month = month - 1
        report_year = year

    month_name = MONTH_NAMES.get(report_month, str(report_month))
    slug = f"monthly-report-{report_year}-{report_month:02d}"
    filename = f"{slug}.html"
    date_str = now.strftime('%Y-%m-%d')

    # Build ETF table rows
    etf_rows = ''
    for e in sorted(etfs, key=lambda x: float(x['yield'] or '0'), reverse=True):
        etf_rows += f'''        <tr><td><strong>{e['code']}</strong></td><td>{e['name']}</td><td style="color:#0891b2;font-weight:700;">{e['yield']}%</td><td>{e['pe']}</td></tr>\n'''

    # Build price table rows
    price_rows = ''
    for code in ['0050','0056','00878','00919','00929','00940','2330','2886','2891']:
        if code in prices:
            p = prices[code]
            change_color = '#10b981' if float(p['change'] or 0) >= 0 else '#ef4444'
            change_sign = '+' if float(p['change'] or 0) >= 0 else ''
            price_rows += f'''        <tr><td><strong>{code}</strong></td><td>{p['name']}</td><td>{p['price']}</td><td style="color:{change_color}">{change_sign}{p['change']}</td></tr>\n'''

    title = f"{report_year} 年 {month_name}台股月報：大盤回顧與存股族觀察"

    html = f'''<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-5WQV8QQDBJ"></script>
  <script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','G-5WQV8QQDBJ');</script>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} - GULICALC</title>
  <meta name="description" content="{report_year}年{month_name}台股回顧：大盤走勢、熱門ETF殖利率排行、存股族操作建議。每月自動更新。">
  <meta property="og:title" content="{title}">
  <meta property="og:description" content="{report_year}年{month_name}台股月報，含ETF殖利率排行與存股建議。">
  <meta property="og:type" content="article">
  <meta property="og:url" content="https://gulicalc.com/articles/{slug}">
  <meta property="og:image" content="https://gulicalc.com/images/og-image.png">
  <meta property="og:locale" content="zh_TW">
  <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large">
  <link rel="icon" type="image/png" sizes="32x32" href="../images/favicon-32.png">
  <link rel="canonical" href="https://gulicalc.com/articles/{slug}">
  <link rel="stylesheet" href="../css/style.css">
  <meta name="google-adsense-account" content="ca-pub-8090613843493309">
  <script>try{{if(localStorage.getItem("gulicalc_theme")==="dark")document.documentElement.setAttribute("data-theme","dark")}}catch(e){{}}</script>
  <script type="application/ld+json">
  [{{
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": "{title}",
    "description": "{report_year}年{month_name}台股回顧：大盤走勢、熱門ETF殖利率排行、存股族操作建議。",
    "url": "https://gulicalc.com/articles/{slug}",
    "datePublished": "{date_str}",
    "dateModified": "{date_str}",
    "image": "https://gulicalc.com/images/og-image.png",
    "author": {{"@type": "Person", "name": "Jacky Chen", "url": "https://gulicalc.com/about"}},
    "publisher": {{"@type": "Organization", "name": "GULICALC", "url": "https://gulicalc.com", "logo": {{"@type": "ImageObject", "url": "https://gulicalc.com/images/logo-nav.png"}}}}
  }},
  {{
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
      {{"@type": "ListItem", "position": 1, "name": "首頁", "item": "https://gulicalc.com/"}},
      {{"@type": "ListItem", "position": 2, "name": "文章", "item": "https://gulicalc.com/articles"}},
      {{"@type": "ListItem", "position": 3, "name": "{title}"}}
    ]
  }}]
  </script>
</head>
<body>
  <header class="site-header">
    <nav class="nav-container">
      <a href="/" class="nav-logo"><img src="../images/logo-nav.png" alt="GULICALC"> <span class="nav-brand">GULICALC</span></a>
      <ul class="nav-links">
        <li><a href="/">首頁</a></li>
        <li><a href="/articles">文章</a></li>
        <li><a href="/about">關於我們</a></li>
      </ul>
    </nav>
  </header>

  <main>
    <nav class="breadcrumb" style="font-size:.82rem;color:#888;padding:.5rem 1rem;max-width:700px;margin:0 auto;">
      <a href="/" style="color:#0891b2;">首頁</a> <span style="margin:0 .3rem;">&rsaquo;</span>
      <a href="/articles" style="color:#0891b2;">文章</a> <span style="margin:0 .3rem;">&rsaquo;</span>
      <span>{title}</span>
    </nav>

    <article style="max-width:700px;margin:0 auto;padding:0 1rem 2rem;">
      <h1 style="font-size:1.5rem;line-height:1.4;margin-bottom:.5rem;">{title}</h1>
      <div style="color:#888;font-size:.85rem;margin-bottom:1.5rem;">{date_str} · 自動生成 · 資料來源：台灣證券交易所</div>

      <p style="background:var(--bg-input,#f1f3f5);border-left:4px solid var(--accent,#0891b2);padding:1rem 1.2rem;border-radius:0 8px 8px 0;font-size:.95rem;line-height:1.7;">
        <strong>本月重點：</strong>以下是 {report_year} 年 {month_name} 台股的關鍵數據，包含大盤走勢、熱門 ETF 殖利率排行、以及存股族的操作建議。資料由系統每月自動從台灣證券交易所抓取更新。
      </p>

      <h2>熱門 ETF 殖利率排行</h2>
      <p>以下是目前熱門存股 ETF 的殖利率排行，資料來自台灣證券交易所即時數據：</p>
      <table style="width:100%;border-collapse:collapse;margin:1rem 0;font-size:.9rem;">
        <tr style="background:var(--bg-input,#f1f3f5);"><th style="padding:.6rem;text-align:left;border-bottom:2px solid var(--border-color,#e5e7eb);">代號</th><th style="padding:.6rem;text-align:left;border-bottom:2px solid var(--border-color,#e5e7eb);">名稱</th><th style="padding:.6rem;text-align:left;border-bottom:2px solid var(--border-color,#e5e7eb);">殖利率</th><th style="padding:.6rem;text-align:left;border-bottom:2px solid var(--border-color,#e5e7eb);">本益比</th></tr>
{etf_rows}      </table>

      <h2>重點標的收盤價</h2>
      <table style="width:100%;border-collapse:collapse;margin:1rem 0;font-size:.9rem;">
        <tr style="background:var(--bg-input,#f1f3f5);"><th style="padding:.6rem;text-align:left;border-bottom:2px solid var(--border-color,#e5e7eb);">代號</th><th style="padding:.6rem;text-align:left;border-bottom:2px solid var(--border-color,#e5e7eb);">名稱</th><th style="padding:.6rem;text-align:left;border-bottom:2px solid var(--border-color,#e5e7eb);">收盤價</th><th style="padding:.6rem;text-align:left;border-bottom:2px solid var(--border-color,#e5e7eb);">漲跌</th></tr>
{price_rows}      </table>

      <h2>存股族本月觀察</h2>
      <ul style="line-height:2;">
        <li>定期定額照常扣款，不要因為大盤高低停扣</li>
        <li>股價上漲代表殖利率下降，重新用<a href="/">計算器</a>算一下</li>
        <li>關注本月除息標的，決定是否參與除息</li>
        <li>長期存股看的是配息穩定度，不是短期股價漲跌</li>
      </ul>

      <h2>相關工具</h2>
      <ul>
        <li><a href="/">股利計算器</a> — 重新算你的殖利率</li>
        <li><a href="/dca-calculator">定期定額試算</a> — 看長期累積效果</li>
        <li><a href="/compound-calculator">複利計算器</a> — 股息再投入模擬</li>
      </ul>

      <h2>延伸閱讀</h2>
      <div style="background:var(--bg-input,#f0fdfa);border:1px solid #ccfbf1;border-radius:12px;padding:1rem 1.2rem;margin:1.5rem 0;">
        <ul style="margin:0;padding-left:1.2rem;font-size:.88rem;line-height:1.8;">
          <li><a href="/articles/top-etf-dividend-yield-2026" style="color:#0891b2;">2026 高殖利率 ETF 排名比較</a></li>
          <li><a href="/articles/stock-saving-recommendations-2026" style="color:#0891b2;">2026 存股推薦：我自己在存的 5 檔</a></li>
          <li><a href="/articles/ex-dividend-calendar-2026" style="color:#0891b2;">2026 除權息日曆</a></li>
          <li><a href="/articles/dividend-yield-ranking-2026" style="color:#0891b2;">台股殖利率排行榜</a></li>
        </ul>
      </div>

      <p style="font-size:.82rem;color:#888;margin-top:2rem;">本頁資料由系統每月自動從台灣證券交易所（TWSE）公開 API 抓取並生成。數據為參考值，實際數字請以證交所官方公告為準。本頁不構成投資建議。</p>
    </article>
  </main>

  <footer class="site-footer">
    <div style="font-size:.78rem;color:#856404;margin-bottom:.5rem;">本站內容僅供參考，不構成任何投資建議。投資有風險，請自行評估。</div>
    <div class="footer-copy">&copy; {year} GULICALC. All rights reserved.</div>
  </footer>

  <script src="../js/theme.js"></script>
</body>
</html>'''

    return filename, slug, html

def update_sitemap(slug, date_str):
    """Add new article to sitemap"""
    with open(SITEMAP_PATH, 'r') as f:
        content = f.read()

    new_url = f'https://gulicalc.com/articles/{slug}'
    if new_url in content:
        print(f"Sitemap already has {slug}")
        return

    entry = f'''  <url>
    <loc>{new_url}</loc>
    <lastmod>{date_str}</lastmod>
    <priority>0.8</priority>
  </url>
</urlset>'''

    content = content.replace('</urlset>', entry)
    with open(SITEMAP_PATH, 'w') as f:
        f.write(content)
    print(f"Sitemap updated: {new_url}")

def main():
    now = datetime.datetime.now()
    print(f"Generating monthly report at {now}")

    # Fetch data
    print("Fetching ETF yields...")
    etfs = get_top_etf_yields()
    print(f"  Got {len(etfs)} ETFs")

    print("Fetching stock prices...")
    prices = get_stock_prices()
    print(f"  Got {len(prices)} stocks")

    if not etfs and not prices:
        print("No data fetched, skipping generation")
        return

    # Generate article
    filename, slug, html = generate_article(now, etfs, prices)
    filepath = os.path.join(ARTICLES_DIR, filename)

    # Check if already exists
    if os.path.exists(filepath):
        print(f"Article already exists: {filename}, overwriting with fresh data")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Article generated: {filename}")

    # Update sitemap
    date_str = now.strftime('%Y-%m-%d')
    update_sitemap(slug, date_str)

    print("Done!")

if __name__ == '__main__':
    main()
