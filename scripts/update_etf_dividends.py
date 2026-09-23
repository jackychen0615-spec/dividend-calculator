#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dividend Automation v2 — 自動更新 data/stocks.json 與 data/etf-div-history.json。

v2 與舊版（v1）最根本的差異：**這支腳本再也不碰 articles/*.html**。

v1 曾經直接用 regex 改寫文章內的計算器預帶值（id="gcP"/"gcD"/"gcY"）、
「股價約 X 元」「殖利率約 X%」等現在式敘述、持股試算表格。這套邏輯完全不
理解網站後來建立的 Data Contract v2.1（window.GULICALC_PAGE_DATA，含
dividendBasis / TTM / FISCAL_YEAR / DISTRIBUTION_YEAR / distributionEvents /
corporateSplit / 現金與股票股利分離）。文章裡帶著日期、年度、口徑、分割
事件的語意，靠扁平 regex 自動推定必然出錯——這正是 2026-09 那次
Production Merge 前發現的 DEPLOY BLOCKER 的根本原因。

v2 把腳本的職責收斂成「更新 Structured Data」：
  - data/etf-div-history.json：純粹的除息事件帳本（symbol → {exDate: amount}），
    只 append/update 有明確日期來源的事件，不推估、不改寫。
  - data/stocks.json：定位為「全站 fallback + 搜尋 metadata」，不是文章的
    canonical source（canonical 是各文章自己人工核准的 GULICALC_PAGE_DATA）。
    更新 dividend 欄位前，必須先知道該 symbol 的 dividendBasis（見
    SYMBOL_POLICIES），口徑不明一律 SKIP + LOG，不用同一套邏輯套用在所有
    標的上。

文章 HTML 一律不寫。frequency / dividendYear 一律保留原值，不自動推導。
"""
import argparse
import json
import os
import ssl
import urllib.error
import urllib.request
from datetime import datetime, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STOCKS = os.path.join(ROOT, "data", "stocks.json")
HISTORY = os.path.join(ROOT, "data", "etf-div-history.json")

# ---------------------------------------------------------------------------
# Data Contract compatibility layer（Step 6）
#
# 每個 symbol 對應它在自己文章頁 window.GULICALC_PAGE_DATA 裡人工核准的
# dividendBasis。這份表是從 42 頁「已核准」production 文章逐頁萃取出來的
# 快照（2026-09-23），不是腳本自己猜的。
#
#   dividendBasis:
#     "TTM"               近12個月逐筆加總（00915/00943）。腳本可以用
#                          etf-div-history.json 的逐日事件機械式重算，因為
#                          這是純加總，沒有詮釋空間。
#     "FISCAL_YEAR"        以官方公告的（某）會計年度配息總額為準。這需要
#                          知道「今年公告的是哪一年度的決議」，光看除息事件
#                          時間序列無法可靠判斷——腳本不自動更新 dividend，
#                          只更新 price。
#     "DISTRIBUTION_YEAR"  以官方公告的（某次）分派為準，常見於金控股的
#                          現金＋股票股利分次決議。同樣不自動更新 dividend。
#     "UNKNOWN"            文章頁尚未採用 v2.1 schema（仍是舊的
#                          annualDividend/dividendYear 欄位），沒有明確口徑
#                          可以依循。SKIP + LOG，dividend 不動；price 仍可
#                          正常更新（股價是客觀市場數據，不需要詮釋）。
#
#   cashOnly: True 代表該 symbol 文章頁的 dividendAmount 欄位定義為「僅現金
#     股利」（v2.1 全站規則）。目前歸類為 TTM/FISCAL_YEAR/DISTRIBUTION_YEAR
#     的 symbol 皆為 cashOnly=True；UNKNOWN 的則未知，不假設。
# ---------------------------------------------------------------------------

SYMBOL_POLICIES = {
    "0050": {"dividendBasis": "UNKNOWN", "cashOnly": False},
    "0056": {"dividendBasis": "UNKNOWN", "cashOnly": False},
    "00713": {"dividendBasis": "UNKNOWN", "cashOnly": False},
    "00878": {"dividendBasis": "UNKNOWN", "cashOnly": False},
    "00919": {"dividendBasis": "UNKNOWN", "cashOnly": False},
    "00929": {"dividendBasis": "UNKNOWN", "cashOnly": False},
    "00934": {"dividendBasis": "UNKNOWN", "cashOnly": False},
    "00936": {"dividendBasis": "UNKNOWN", "cashOnly": False},
    "00939": {"dividendBasis": "UNKNOWN", "cashOnly": False},
    "00940": {"dividendBasis": "UNKNOWN", "cashOnly": False},
    "006208": {"dividendBasis": "UNKNOWN", "cashOnly": False},
    "2881": {"dividendBasis": "FISCAL_YEAR", "cashOnly": True},
    "2882": {"dividendBasis": "UNKNOWN", "cashOnly": False},
    "2884": {"dividendBasis": "DISTRIBUTION_YEAR", "cashOnly": True},
    "2886": {"dividendBasis": "UNKNOWN", "cashOnly": False},
    "2891": {"dividendBasis": "UNKNOWN", "cashOnly": False},
    "2892": {"dividendBasis": "UNKNOWN", "cashOnly": False},
    "5880": {"dividendBasis": "DISTRIBUTION_YEAR", "cashOnly": True},
    "2330": {"dividendBasis": "UNKNOWN", "cashOnly": False},
    "2317": {"dividendBasis": "UNKNOWN", "cashOnly": False},
    "2382": {"dividendBasis": "FISCAL_YEAR", "cashOnly": True},
    "2454": {"dividendBasis": "FISCAL_YEAR", "cashOnly": True},
    "1216": {"dividendBasis": "UNKNOWN", "cashOnly": False},
    "1301": {"dividendBasis": "UNKNOWN", "cashOnly": False},
    "2412": {"dividendBasis": "FISCAL_YEAR", "cashOnly": True},
    "00900": {"dividendBasis": "UNKNOWN", "cashOnly": False},
    "00915": {"dividendBasis": "TTM", "cashOnly": True},
    "00918": {"dividendBasis": "UNKNOWN", "cashOnly": False},
    "00932": {"dividendBasis": "UNKNOWN", "cashOnly": False},
    "00943": {"dividendBasis": "TTM", "cashOnly": True},
    "00927": {"dividendBasis": "UNKNOWN", "cashOnly": False},
    "2308": {"dividendBasis": "FISCAL_YEAR", "cashOnly": True},
}

TTM_MIN_COVERAGE_DAYS = 330  # 少於這個天數視為「資料不足12個月」，SKIP


def policy_for(code):
    return SYMBOL_POLICIES.get(code, {"dividendBasis": "UNKNOWN", "cashOnly": False})


def _num(x):
    x = float(x)
    return int(x) if x == int(x) else round(x, 4)


# ---------------------------------------------------------------------------
# TWSE 官方來源
# ---------------------------------------------------------------------------
PRICE_URL = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
EXDIV_URL = "https://openapi.twse.com.tw/v1/exchangeReport/TWT48U_ALL"
BACKFILL_URL = "https://www.twse.com.tw/rwd/zh/exRight/TWT49U?startDate={start}&endDate={end}&response=json"


def fetch(url):
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "gulicalc-bot-v2"})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.URLError as e:
        if "CERTIFICATE_VERIFY_FAILED" not in str(e):
            raise
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, timeout=40, context=ctx) as r:
            return json.loads(r.read().decode("utf-8"))


def roc_to_iso(d):
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


# ---------------------------------------------------------------------------
# Step 4 — etf-div-history.json：純粹的除息事件帳本
# 只 append 有明確日期＋來源的事件；不推估、不年化、不改文章。
# 這部分邏輯沿用 v1（原本就是機械式逐日累積，符合「只記錄有日期的事實」的
# 要求，不需要重寫），唯一差異是 v2 明確標註每筆事件的 source。
# ---------------------------------------------------------------------------

def backfill_history(history, start, end, dry_run, log):
    try:
        rows = fetch(BACKFILL_URL.format(start=start, end=end)).get("data") or []
    except Exception as e:
        log(f"歷史除權息回補失敗，略過：{e}")
        return 0
    added = 0
    for r in rows:
        if len(r) < 7 or r[6] != "息":
            continue  # 只要純現金股息；除權或權息合併的權值不是現金
        code = r[1]
        try:
            iso = roc_to_iso(r[0].replace("年", "").replace("月", "").replace("日", ""))
            amount = float(r[5])
        except (ValueError, TypeError, AttributeError):
            continue
        if not iso or amount <= 0:
            continue
        history.setdefault(code, {})
        if iso not in history[code]:
            if not dry_run:
                history[code][iso] = round(amount, 4)
            added += 1
    log(f"歷史回補：{'將新增' if dry_run else '新增'} {added} 筆除息事件（來源：TWSE TWT49U）。")
    return added


def append_daily_events(history, exdiv_rows, dry_run, log):
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
            if not dry_run:
                history[c][iso] = round(amt, 4)
            new_events += 1
    log(f"當日除息事件：{'將新增' if dry_run else '新增'} {new_events} 筆（來源：TWSE TWT48U_ALL）。")
    return new_events


# ---------------------------------------------------------------------------
# Step 5/8 — stocks.json：dividendBasis-aware 更新 + safety guards
# ---------------------------------------------------------------------------

def compute_ttm(history, code, cutoff_date):
    """TTM 是純粹的逐日事件加總，機械式、無詮釋空間，可以安全自動算。
    回傳 (ttm_value, coverage_ok, reason_if_not_ok)。
    """
    evs = history.get(code, {})
    if not evs:
        return None, False, "無歷史除息事件"
    span_days = (datetime.utcnow().date() - datetime.strptime(min(evs), "%Y-%m-%d").date()).days
    if span_days < TTM_MIN_COVERAGE_DAYS:
        return None, False, f"TTM資料不足12個月（現有回溯 {span_days} 天，需≥{TTM_MIN_COVERAGE_DAYS}天）"
    ttm = round(sum(a for d, a in evs.items() if d >= cutoff_date), 4)
    if ttm <= 0:
        return None, False, "TTM視窗內加總為0"
    return ttm, True, None


def update_stocks(stocks_data, price_map, history, cutoff_date, dry_run, log):
    """依 dividendBasis 逐檔更新 price / dividend / dividendYield。
    frequency / dividendYear 一律不動（保留原值，不自行猜測）。
    """
    changes = []  # for dry-run report: dict(code, field, old, new, source, basis, reason)
    price_upd = div_upd = skipped = 0

    for s in stocks_data.get("stocks", []):
        code = s.get("code")
        pol = policy_for(code)
        basis = pol["dividendBasis"]

        # --- Price: 客觀市場數據，任何 basis 都可以更新，不需要詮釋 ---
        lp = price_map.get(code)
        old_price = float(s.get("price", 0) or 0)
        if lp and lp > 0 and abs(lp - old_price) > 0.001:
            changes.append({
                "code": code, "field": "price", "old": old_price, "new": lp,
                "source": "TWSE STOCK_DAY_ALL", "basis": basis, "reason": "最新收盤價",
            })
            if not dry_run:
                s["price"] = lp
            price_upd += 1
            new_price = lp
        else:
            new_price = old_price

        # --- Dividend: 依 basis 決定是否自動更新 ---
        old_div = float(s.get("dividend", 0) or 0)

        if basis == "TTM":
            ttm, ok, reason = compute_ttm(history, code, cutoff_date)
            if not ok:
                log(f"SKIP {code}（TTM）：{reason}")
                skipped += 1
            elif abs(ttm - old_div) > 0.0005:
                changes.append({
                    "code": code, "field": "dividend", "old": old_div, "new": ttm,
                    "source": "etf-div-history.json 近12個月逐筆加總", "basis": basis,
                    "reason": f"TTM機械式重算（視窗 {cutoff_date} 至今）",
                })
                if not dry_run:
                    s["dividend"] = ttm
                div_upd += 1
                new_div = ttm
            else:
                new_div = old_div
        elif basis in ("FISCAL_YEAR", "DISTRIBUTION_YEAR"):
            # 這兩種口徑需要知道「官方公告的是哪一次／哪一年度決議」，光看
            # TWSE 除息事件時間序列無法可靠判斷是哪個年度的決議，不猜。
            log(f"SKIP {code}（{basis}）：僅逐日除息事件無法可靠判定官方公告年度/分派期別，dividend 不自動更新，維持人工核准值。")
            skipped += 1
            new_div = old_div
        else:  # UNKNOWN
            log(f"SKIP {code}（dividendBasis unknown）：文章頁尚未採用 Data Contract v2.1 schema，口徑不明，dividend 不自動更新。")
            skipped += 1
            new_div = old_div

        # --- dividendYield：純衍生值（dividend÷price×100），用當下的 dividend
        # （不論是否剛更新）與 price 重算，這不是詮釋性判斷，只是維持內部一致 ---
        if new_price > 0 and new_div > 0:
            new_yield = round(new_div / new_price * 100, 2)
            old_yield = s.get("dividendYield")
            if old_yield is None or abs(old_yield - new_yield) > 0.005:
                changes.append({
                    "code": code, "field": "dividendYield", "old": old_yield, "new": new_yield,
                    "source": "derived: dividend/price*100", "basis": basis,
                    "reason": "維持與 price/dividend 內部一致（衍生值，非獨立判斷）",
                })
                if not dry_run:
                    s["dividendYield"] = new_yield

        # frequency / dividendYear：一律不動。
        # （Step 5 明確要求：如果無法可靠推導，保留原值，不自行猜測；
        #  這兩個欄位需要理解配息週期語意，這支腳本不做。）

    return changes, price_upd, div_upd, skipped


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="只顯示會做的變更，不寫檔、不 commit、不 push")
    args = ap.parse_args()
    dry_run = args.dry_run

    logs = []
    def log(msg):
        logs.append(msg)
        print(msg)

    log(f"=== Dividend Automation v2 {'(DRY RUN)' if dry_run else ''} ===")
    log("本腳本只更新 data/stocks.json 與 data/etf-div-history.json，不寫入 articles/*.html。")

    stocks_data = load_json(STOCKS, {"stocks": []})
    history = load_json(HISTORY, {})

    try:
        price_rows = fetch(PRICE_URL)
        exdiv_rows = fetch(EXDIV_URL)
    except Exception as e:
        log(f"TWSE API 取得失敗，略過本次更新：{e}")
        return

    price_map = {}
    for it in price_rows:
        c = it.get("Code")
        p = (it.get("ClosingPrice") or "").replace(",", "")
        try:
            price_map[c] = float(p)
        except (ValueError, TypeError):
            pass

    new_events = append_daily_events(history, exdiv_rows, dry_run, log)

    cutoff = (datetime.utcnow() - timedelta(days=365)).strftime("%Y-%m-%d")

    # 只有 TTM basis 的 symbol 需要確保歷史涵蓋足夠——其餘 basis 不靠這份
    # 歷史檔自動算 dividend，回補與否不影響它們。
    ttm_codes = [c for c, p in SYMBOL_POLICIES.items() if p["dividendBasis"] == "TTM"]
    if any(not history.get(code) or min(history[code]) >= cutoff for code in ttm_codes):
        backfill_history(
            history,
            (datetime.utcnow() - timedelta(days=400)).strftime("%Y%m%d"),
            datetime.utcnow().strftime("%Y%m%d"),
            dry_run, log,
        )

    changes, price_upd, div_upd, skipped = update_stocks(stocks_data, price_map, history, cutoff, dry_run, log)

    if dry_run:
        log("")
        log("=== Dry-run 變更清單 ===")
        if not changes:
            log("（無任何變更）")
        for c in changes:
            log(
                f"  [{c['code']}] {c['field']}: {c['old']!r} -> {c['new']!r}"
                f" | basis={c['basis']} | source={c['source']} | reason={c['reason']}"
            )
        log("")
        log("受影響檔案（dry-run 不會真的寫入）：")
        log("  data/stocks.json" if any(c["field"] in ("price", "dividend", "dividendYield") for c in changes) else "  （stocks.json 無變更）")
        log("  data/etf-div-history.json" if new_events else "  （etf-div-history.json 無變更）")
        log("  articles/*.html: 0（v2 不再寫入文章）")
        log("")
        log(f"完成（dry-run）：股價 {price_upd} 檔、配息 {div_upd} 檔、略過 {skipped} 檔。")
        return

    stocks_data["lastUpdated"] = datetime.utcnow().strftime("%Y-%m-%d")

    with open(STOCKS, "w", encoding="utf-8") as f:
        json.dump(stocks_data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    with open(HISTORY, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
        f.write("\n")

    log(f"完成：新增除息事件 {new_events}、更新股價 {price_upd} 檔、更新配息 {div_upd} 檔、略過 {skipped} 檔（口徑不明或需人工判斷）。")


if __name__ == "__main__":
    main()
