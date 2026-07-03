#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
線上計算器健檢：檢查每個計算器頁能否正常載入且關鍵元素在、共用資產與 API 正常。
壞掉就 Telegram 警告站長（需環境變數 TG_BOT_TOKEN、TG_CHAT_ID）。
由 GitHub Actions 定期執行（雲端、不需本機）。全部用標準庫。
"""
import json
import os
import ssl
import time
import urllib.request

BASE = "https://gulicalc.com"

# 頁面 → 必須出現的關鍵元素（缺任一 = 該計算器可能壞了）
PAGES = {
    "/": ['id="stockPrice"', 'id="dividend"', 'id="shares"', 'id="calcResults"', "js/calculator.js"],
    "/compound-calculator": ['id="monthlyInvestment"', 'id="years"', "compound-calculator.js"],
    "/dca-calculator": ['id="monthlyAmount"', 'id="investYears"', "dca-calculator.js"],
    "/payback-calculator": ['id="buyPrice"', 'id="holdShares"', "payback-calculator.js"],
    "/mortgage-calculator": ['id="loanAmount"', 'id="interestRate"', 'id="monthlyPayment"'],
    "/tax-calculator": ['id="dividendIncome"', 'id="taxResult"', 'id="effectiveRate"'],
    "/compare": ['id="compareResult"'],
    "/goal": ['id="goalAmount"', 'id="goalResult"'],
    "/embed/": ['id="p"', 'id="d"'],
    # 抽樣個股內嵌計算器（striking-distance 主力頁）
    "/articles/tsmc-dividend-calculator": ['id="gcP"', 'id="gcD"'],
    "/articles/0056-dividend-calculator": ['id="gcP"'],
    "/articles/hon-hai-dividend": ['id="gcP"'],
}

# 共用資產：載不到（非 200）= 計算器會壞
ASSETS = [
    "/js/calculator.js",
    "/css/style.css",
    "/js/compound-calculator.js",
    "/js/dca-calculator.js",
    "/js/payback-calculator.js",
    "/js/stock-search.js",
]

CTX = ssl.create_default_context()


def fetch(url, retries=2):
    """回傳 (status, body)；重試以避開暫時性抖動。失敗回 (None, err字串)。"""
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "gulicalc-healthcheck"})
            with urllib.request.urlopen(req, timeout=25, context=CTX) as r:
                return r.status, r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            return e.code, ""
        except Exception as e:
            last = str(e)
            time.sleep(4 * (i + 1))
    return None, last


def main():
    fails = []

    # 1) 計算器頁
    for path, needles in PAGES.items():
        status, body = fetch(BASE + path)
        if status != 200:
            fails.append(f"❌ {path} → HTTP {status}")
            continue
        missing = [n for n in needles if n not in body]
        if missing:
            fails.append(f"⚠️ {path} → 缺元素：{', '.join(missing)}")

    # 2) 共用資產
    for a in ASSETS:
        status, _ = fetch(BASE + a)
        if status != 200:
            fails.append(f"❌ 資產 {a} → HTTP {status}")

    # 3) /api/stocks（帶入功能靠它）
    status, body = fetch(BASE + "/api/stocks")
    if status != 200:
        fails.append(f"❌ /api/stocks → HTTP {status}")
    else:
        try:
            data = json.loads(body)
            n = len(data.get("stocks", []))
            if n < 100:
                fails.append(f"⚠️ /api/stocks → 只回 {n} 檔（疑異常，應上千）")
        except Exception:
            fails.append("❌ /api/stocks → 回傳非合法 JSON")

    # 結果
    if not fails:
        print(f"✅ 健檢通過：{len(PAGES)} 頁計算器、{len(ASSETS)} 個資產、API 皆正常。")
        return 0

    report = "🚨 gulicalc 計算器健檢發現問題：\n\n" + "\n".join(fails) + f"\n\n（共 {len(fails)} 項，請盡快檢查）"
    print(report)

    token, chat = os.environ.get("TG_BOT_TOKEN"), os.environ.get("TG_CHAT_ID")
    if token and chat:
        try:
            data = json.dumps({"chat_id": chat, "text": report, "disable_web_page_preview": True}).encode()
            req = urllib.request.Request(
                f"https://api.telegram.org/bot{token}/sendMessage",
                data=data, headers={"Content-Type": "application/json"},
            )
            urllib.request.urlopen(req, timeout=20, context=CTX)
            print("已 Telegram 警告站長。")
        except Exception as e:
            print("Telegram 發送失敗：", e)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
