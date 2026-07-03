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
import re
import ssl
import urllib.request
from datetime import datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STOCKS = os.path.join(ROOT, "data", "stocks.json")
HISTORY = os.path.join(ROOT, "data", "etf-div-history.json")
ARTICLES_DIR = os.path.join(ROOT, "articles")

# 個股文章 → 股票代號（僅這些含內嵌計算器的頁面會被自動校正數字）
STOCK_ARTICLES = {
    "2330": "tsmc-dividend-calculator.html",
    "2317": "hon-hai-dividend.html",
    "2412": "chunghwa-telecom-dividend.html",
    "2454": "mediatek-dividend.html",
    "2308": "delta-electronics-dividend.html",
    "5880": "taiwan-coop-dividend.html",
}


def _num(x):
    x = float(x)
    return int(x) if x == int(x) else round(x, 2)


def patch_articles(by_code):
    """把個股文章內文與計算器預帶值校正到現值。保守：對不上格式就不動。"""
    changed = 0
    for code, fn in STOCK_ARTICLES.items():
        info = by_code.get(code)
        if not info:
            continue
        price, div = info
        if not price or price <= 0 or not div or div <= 0:
            continue
        path = os.path.join(ARTICLES_DIR, fn)
        try:
            with open(path, encoding="utf-8") as f:
                h = orig = f.read()
        except FileNotFoundError:
            continue
        pn, dn = _num(price), _num(div)
        y = round(div / price * 100, 2)
        cost = f"{int(round(price * 1000)):,}"
        tot = f"{int(round(div * 1000)):,}"
        # 計算器 input 預帶值（JS 會依此重算殖利率/成本/年領）
        h = re.sub(r'(id="gcP"[^>]*value=")[\d.]+(")', rf"\g<1>{pn}\g<2>", h)
        h = re.sub(r'(id="gcD"[^>]*value=")[\d.]+(")', rf"\g<1>{dn}\g<2>", h)
        # 計算器初始顯示（爬蟲看得到的初值）
        h = re.sub(r'(id="gcY">)[\d.]+(<)', rf"\g<1>{y}\g<2>", h)
        h = re.sub(r'(id="gcC">)[\d,]+(<)', rf"\g<1>{cost}\g<2>", h)
        h = re.sub(r'(id="gcT">)[\d,]+(<)', rf"\g<1>{tot}\g<2>", h)
        # 計算器標頭文字「股價 X、年配息 Y 元」（此措辭只出現在計算器區塊，安全）
        h = re.sub(r"股價\s*[\d.]+、年配息\s*[\d.]+\s*元", f"股價 {pn}、年配息 {dn} 元", h, count=1)
        # 注意：不自動改內文敘述（股價約/殖利率約…）。這些 regex 在無人看管下可能
        # 誤命中 head 的 JSON-LD schema 造成不一致，內文由人工定期校正即可（措辭為「約」漂移慢）。
        if h != orig:
            with open(path, "w", encoding="utf-8") as f:
                f.write(h)
            changed += 1
            print(f"  校正文章：{fn} → 股價{pn}/配息{dn}/殖利率{round(y, 1)}%")
    print(f"文章數字校正 {changed} 篇。")

PRICE_URL = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
EXDIV_URL = "https://openapi.twse.com.tw/v1/exchangeReport/TWT48U_ALL"
# 個股官方殖利率（近一年現金股利/收盤價）；ETF 不在此表。用來校正個股配息比除息累積可靠。
BWIBBU_URL = "https://openapi.twse.com.tw/v1/exchangeReport/BWIBBU_ALL"


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
    try:
        bwibbu_rows = fetch(BWIBBU_URL)
    except Exception as e:
        print("BWIBBU 取得失敗，個股配息校正略過：", e)
        bwibbu_rows = []

    price_map = {}
    for it in price_rows:
        c = it.get("Code")
        p = it.get("ClosingPrice", "").replace(",", "")
        try:
            price_map[c] = float(p)
        except (ValueError, TypeError):
            pass

    # 個股官方殖利率（%）；ETF 不在此表，get 會是 None → 自動跳過
    yield_map = {}
    for it in bwibbu_rows:
        try:
            yield_map[it.get("Code")] = float(it.get("DividendYield", "0"))
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
        # 3) 個股：用官方殖利率×現價校正配息（比除息累積可靠；ETF 不在 BWIBBU 會自動跳過）
        yv = yield_map.get(code)
        cur_price = price_map.get(code) or float(s.get("price", 0))
        if yv and yv > 0 and cur_price > 0:
            official = round(cur_price * yv / 100, 2)
            cur_div = float(s.get("dividend", 0))
            # 官方配息=殖利率×價=實際年配息（不隨股價變、很穩）。差 >12% 才覆蓋，
            # 保留乾淨的正確種子值（如台積電 22），只修明顯錯的（聯發科、台塑、合庫金…）。
            if official > 0 and abs(official - cur_div) > max(0.08, cur_div * 0.12):
                s["dividend"] = official
                div_upd += 1

    stocks_data["lastUpdated"] = datetime.utcnow().strftime("%Y-%m-%d")

    with open(STOCKS, "w", encoding="utf-8") as f:
        json.dump(stocks_data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    with open(HISTORY, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
        f.write("\n")

    # 用最新的 stocks.json 現值，順手把個股文章的數字校正到現值（不再手動維護）
    by_code = {
        s.get("code"): (float(s.get("price", 0) or 0), float(s.get("dividend", 0) or 0))
        for s in stocks_data.get("stocks", [])
    }
    patch_articles(by_code)

    print(f"完成：新增除息事件 {new_events}、更新股價 {price_upd} 檔、更新配息 {div_upd} 檔。")


if __name__ == "__main__":
    main()
