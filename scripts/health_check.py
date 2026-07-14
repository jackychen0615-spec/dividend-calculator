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

    # 3) /api/stocks（帶入功能靠它）+ 資料合理性檢查
    # 緣由：2026/7 曾發生 change 欄位(絕對點數)被前端當百分比顯示，95 檔股票
    # 出現「大立光 +395%」這種超過台股單日 ±10% 上限的不可能數字，修好後補這道防線。
    status, body = fetch(BASE + "/api/stocks")
    if status != 200:
        fails.append(f"❌ /api/stocks → HTTP {status}")
    else:
        try:
            data = json.loads(body)
            stocks = data.get("stocks", [])
            n = len(stocks)
            if n < 100:
                fails.append(f"⚠️ /api/stocks → 只回 {n} 檔（疑異常，應上千）")

            no_field = sum(1 for s in stocks if "changePercent" not in s)
            if no_field > n * 0.5:
                fails.append(f"❌ /api/stocks → {no_field}/{n} 檔缺少 changePercent 欄位（疑似欄位被移除或快取卡住舊版）")

            impossible = [
                s for s in stocks
                if s.get("changePercent") is not None and abs(s.get("changePercent") or 0) > 15
            ]
            if len(impossible) > 3:
                examples = ", ".join(f"{s.get('code')}{s.get('name')}={s.get('changePercent')}%" for s in impossible[:5])
                fails.append(
                    f"❌ /api/stocks → {len(impossible)} 檔漲跌幅超過±15%（台股單日上限±10%，疑似單位算錯）：{examples}"
                )

            bad_yield = [
                s for s in stocks
                if s.get("dividendYield") is not None and (s.get("dividendYield") or 0) > 30
            ]
            if len(bad_yield) > 3:
                examples = ", ".join(f"{s.get('code')}{s.get('name')}={s.get('dividendYield')}%" for s in bad_yield[:5])
                fails.append(f"⚠️ /api/stocks → {len(bad_yield)} 檔殖利率超過30%（疑似資料異常）：{examples}")
        except Exception:
            fails.append("❌ /api/stocks → 回傳非合法 JSON")

    # 4) /api/etf-dividends 資料合理性
    status, body = fetch(BASE + "/api/etf-dividends")
    if status != 200:
        fails.append(f"❌ /api/etf-dividends → HTTP {status}")
    else:
        try:
            data = json.loads(body)
            etfs = data.get("data", {})
            if len(etfs) < 5:
                fails.append(f"⚠️ /api/etf-dividends → 只回 {len(etfs)} 檔（疑異常）")
            bad = [
                (code, v.get("yield")) for code, v in etfs.items()
                if v.get("yield") is not None and (v.get("yield") > 20 or v.get("yield") < 0)
            ]
            if bad:
                fails.append(f"⚠️ /api/etf-dividends → 殖利率異常：{bad}")
        except Exception:
            fails.append("❌ /api/etf-dividends → 回傳非合法 JSON")

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
