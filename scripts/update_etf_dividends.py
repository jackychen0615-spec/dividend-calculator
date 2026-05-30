#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自動更新 ETF/個股的「即時股價」與「近一年配息」到 data/stocks.json。

資料來源（TWSE 公開 API）：
  - STOCK_DAY_ALL：當日收盤價（含 ETF）
  - TWT48U_ALL：除權除息預告表（含 ETF 的現金股利 CashDividend）

機制：
  - 除息表只列「近期」事件，故將每天看到的除息事件累積到
    data/etf-div-history.json，再以「近 365 天加總」算出近一年配息。
  - 股價：每次都用最新收盤價更新（即時、立即準）。
  - 配息：歷史累積足夠後才覆蓋（避免初期資料不全而低估）。

由 GitHub Actions 每日排程執行，無需手動維護。
"""
import json
import os
import ssl
import urllib.request
from datetime import datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STOCKS = os.path.join(ROOT, "data", "stocks.json")
HISTORY = os.path.join(ROOT, "data", "etf-div-history.json")

PRICE_URL = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
EXDIV_URL = "https://openapi.twse.com.tw/v1/exchangeReport/TWT48U_ALL"


def fetch(url):
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "gulicalc-bot"})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.URLError as e:
        # 部分環境(如本機 macOS)憑證鏈驗證失敗，對公開唯讀 API 做後備
        if "CERTIFICATE_VERIFY_FAILED" not in str(e):
            raise
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, timeout=40, context=ctx) as r:
            return json.loads(r.read().decode("utf-8"))


def roc_to_iso(d):
    # 民國日期 1150602 -> 2026-06-02
    d = str(d).strip()
    if len(d) == 7:
        return f"{int(d[:3]) + 1911:04d}-{d[3:5]}-{d[5:7]}"
    return None


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def main():
    stocks_data = load_json(STOCKS, {"stocks": []})
    history = load_json(HISTORY, {})  # { code: { "YYYY-MM-DD": amount } }

    try:
        price_rows = fetch(PRICE_URL)
        exdiv_rows = fetch(EXDIV_URL)
    except Exception as e:
        print("TWSE API 取得失敗，略過本次更新：", e)
        return

    price_map = {}
    for it in price_rows:
        c = it.get("Code")
        p = it.get("ClosingPrice", "").replace(",", "")
        try:
            price_map[c] = float(p)
        except (ValueError, TypeError):
            pass

    # 累積除息事件（去重）
    new_events = 0
    for it in exdiv_rows:
        c = it.get("Code")
        cash = (it.get("CashDividend") or "").replace(",", "")
        iso = roc_to_iso(it.get("Date"))
        try:
            amt = float(cash)
        except (ValueError, TypeError):
            amt = 0
        if not c or not iso or amt <= 0:
            continue
        history.setdefault(c, {})
        if iso not in history[c]:
            history[c][iso] = round(amt, 4)
            new_events += 1

    cutoff = (datetime.utcnow() - timedelta(days=365)).strftime("%Y-%m-%d")

    price_upd = div_upd = 0
    for s in stocks_data.get("stocks", []):
        code = s.get("code")
        # 1) 股價：一律更新為最新收盤價
        lp = price_map.get(code)
        if lp and lp > 0 and abs(lp - float(s.get("price", 0))) > 0.001:
            s["price"] = lp
            price_upd += 1
        # 2) 配息：近 365 天累積（僅在累積到合理值時覆蓋，避免初期低估）
        evs = history.get(code, {})
        ttm = round(sum(a for d, a in evs.items() if d >= cutoff), 2)
        if ttm > 0 and ttm >= float(s.get("dividend", 0)) * 0.6:
            if abs(ttm - float(s.get("dividend", 0))) > 0.001:
                s["dividend"] = ttm
                div_upd += 1

    stocks_data["lastUpdated"] = datetime.utcnow().strftime("%Y-%m-%d")

    with open(STOCKS, "w", encoding="utf-8") as f:
        json.dump(stocks_data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    with open(HISTORY, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"完成：新增除息事件 {new_events}、更新股價 {price_upd} 檔、更新配息 {div_upd} 檔。")


if __name__ == "__main__":
    main()
