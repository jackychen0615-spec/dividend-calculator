#!/usr/bin/env python3
"""
除息行事曆產生器
1. 除息日：證交所 TWT48U（預告）＋ TWT49U（已除息），以證交所為準
2. 配息金額：以證交所為準；未除息且證交所寫「待公告」就寫待公告（不用 Yahoo，Yahoo 可能是估計值）；
   已除息的權息股，證交所只給權值+息值，現金部分才用 Yahoo
3. 發放日：Yahoo 股市（cashPayDate），沒有就寫「待公告」

輸出：
- data/dividend-events.json
- cal/<代號>.ics、cal/all.ics（站內有個股頁的標的，可訂閱）
- articles/ex-dividend-YYYY-MM.html 內 <!-- EVENTS:START --> ～ <!-- EVENTS:END --> 之間的表格

用法：python3 scripts/build_dividend_calendar.py --month 2026-11
HTTPS 一律用 curl（urllib 打證交所會 SSL 驗證失敗）。
"""
import argparse, datetime as dt, glob, html, json, os, re, subprocess, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"


def curl(url):
    for _ in range(3):
        r = subprocess.run(["curl", "-s", "-A", UA, "--max-time", "30", url], capture_output=True)
        if r.returncode == 0 and r.stdout:
            return r.stdout.decode("utf-8", "replace")
        time.sleep(2)
    raise RuntimeError("fetch failed: " + url)


def roc(s):  # '115年11月17日' -> date
    y, m, d = map(int, re.findall(r"\d+", s))
    return dt.date(y + 1911, m, d)


def num(s):
    try:
        v = float(s)
        return v if v > 0 else None
    except (TypeError, ValueError):
        return None


def site_pages():
    """代號 -> 文章 slug（從 GULICALC_PAGE_DATA.symbol 抓）"""
    out = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "articles", "*.html"))):
        if "prototype" in f:
            continue
        m = re.search(r'symbol: "([0-9A-Z]+)"', open(f, encoding="utf-8").read())
        if m:
            out.setdefault(m.group(1), os.path.basename(f)[:-5])
    return out


def twse_events(start, end):
    ev = {}
    d = json.loads(curl("https://www.twse.com.tw/rwd/zh/exRight/TWT48U?response=json"))
    for r in d.get("data", []):
        day = roc(r[0])
        if start <= day <= end:
            ev[(r[1].strip(), day)] = {"code": r[1].strip(), "name": r[2].strip(), "kind": r[3],
                                       "ex": day, "cash": num(r[7]), "stock_rate": num(r[4])}
    time.sleep(1.5)
    d = json.loads(curl("https://www.twse.com.tw/rwd/zh/exRight/TWT49U?startDate=%s&endDate=%s&response=json"
                        % (start.strftime("%Y%m%d"), end.strftime("%Y%m%d"))))
    for r in d.get("data", []):
        day = roc(r[0])
        key = (r[1].strip(), day)
        e = ev.setdefault(key, {"code": key[0], "name": r[2].strip(), "kind": r[6], "ex": day,
                                "cash": None, "stock_rate": None})
        if r[6] == "息" and e["cash"] is None:
            e["cash"] = num(r[5])  # 純除息時「權值+息值」就是現金股利
    return ev


def yahoo(code):
    """回傳 {除息日: (現金股利, 發放日)}"""
    t = curl("https://tw.stock.yahoo.com/quote/%s/dividend" % code)
    key = '"dividend-combineCashAndStock--payYear-%s.TW-true":' % code
    i = t.find(key)
    if i < 0:
        return {}
    data, _ = json.JSONDecoder().raw_decode(t[i + len(key):])
    out = {}
    for x in data.get("data", {}).get("dividends", []):
        # 季配/月配是 SUB 筆、年配個股是 YEAR 筆，都以 exDividend.date 為除息日
        exd = x.get("exDividend") or {}
        if not exd.get("date"):
            continue
        ed = dt.date.fromisoformat(exd["date"][:10])
        pay = exd.get("cashPayDate")
        out[ed] = (num(exd.get("cash")), dt.date.fromisoformat(pay[:10]) if pay else None)
    return out


HOLIDAYS = set()


def load_holidays():
    """證交所休市日（名稱含「交易日」的是開始/最後交易日，不是休市）"""
    try:
        for h in json.loads(curl("https://openapi.twse.com.tw/v1/holidaySchedule/holidaySchedule").lstrip("\ufeff")):
            if "交易日" not in h["Name"]:
                HOLIDAYS.add(roc_compact(h["Date"]))
    except Exception as ex:
        print("holiday fetch fail, weekends only:", ex)


def roc_compact(s):  # '1151225' -> date
    return dt.date(int(s[:-4]) + 1911, int(s[-4:-2]), int(s[-2:]))


def last_buy_day(ex):
    d = ex - dt.timedelta(days=1)
    while d.weekday() > 4 or d in HOLIDAYS:
        d -= dt.timedelta(days=1)
    return d


def esc(s):
    return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def fold(line):
    """RFC 5545：每行最多 75 bytes，續行以空白開頭"""
    out, cur = [], b""
    for ch in line:
        c = ch.encode("utf-8")
        if len(cur) + len(c) > (75 if not out else 74):
            out.append(cur.decode("utf-8")); cur = b""
        cur += c
    out.append(cur.decode("utf-8"))
    return "\r\n ".join(out)


def ics(events, title):
    L = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//gulicalc.com//dividend calendar//ZH",
         "CALSCALE:GREGORIAN", "METHOD:PUBLISH", "X-WR-CALNAME:" + title, "X-WR-TIMEZONE:Asia/Taipei",
         "REFRESH-INTERVAL;VALUE=DURATION:P1D", "X-PUBLISHED-TTL:P1D"]
    def add(uid, day, summary, desc, alarm):
        L.extend(["BEGIN:VEVENT", "UID:%s@gulicalc.com" % uid, "DTSTAMP:" + day.strftime("%Y%m%d") + "T000000Z",  # 固定值，資料沒變就不產生 diff
                  "DTSTART;VALUE=DATE:" + day.strftime("%Y%m%d"),
                  "DTEND;VALUE=DATE:" + (day + dt.timedelta(days=1)).strftime("%Y%m%d"),
                  "SUMMARY:" + esc(summary), "DESCRIPTION:" + esc(desc)])
        if alarm:  # 當天早上 9 點提醒（全天事件從 00:00 起算）
            L.extend(["BEGIN:VALARM", "ACTION:DISPLAY", "DESCRIPTION:" + esc(summary), "TRIGGER:PT9H", "END:VALARM"])
        L.append("END:VEVENT")
    for e in events:
        cash = "%s 元" % fmt(e["cash"]) if e["cash"] else "金額待公告"
        url = "https://gulicalc.com/articles/%s" % e["slug"] if e.get("slug") else "https://gulicalc.com/"
        lb = last_buy_day(e["ex"])
        add("buy-%s-%s" % (e["code"], e["ex"].isoformat()), lb, "%s 最後買進日（%s 除息）" % (e["code"], e["ex"].strftime("%-m/%-d")),
            "%s %s 將在 %s 除息（%s）。今天收盤時持有，才領得到這次配息。\n試算：%s" % (e["code"], e["name"], e["ex"].strftime("%-m/%-d"), cash, url), True)
        add("ex-%s-%s" % (e["code"], e["ex"].isoformat()), e["ex"], "%s %s 除息（%s）" % (e["code"], e["name"], cash),
            "今天是除息交易日，開盤參考價會扣除配息。\n" + url, False)
        if e.get("pay"):
            add("pay-%s-%s" % (e["code"], e["pay"].isoformat()), e["pay"], "%s %s 股利發放（%s）" % (e["code"], e["name"], cash),
                "現金股利預計今天匯入交割銀行帳戶（扣匯費與二代健保補充保費後）。\n" + url, False)
    L.append("END:VCALENDAR")
    return "\r\n".join(fold(l) for l in L) + "\r\n"


def fmt(v):
    return ("%.4f" % v).rstrip("0").rstrip(".")


def render_rows(events, pages):
    def row(e, i):
        bg = ' style="background:#fafafa;"' if i % 2 else ""
        S = "padding:6px;border:1px solid #ddd;"
        N = S + "white-space:normal;"  # 手機版讓名稱換行，發放日欄才不會被擠出畫面
        name = "%s %s" % (e["code"], html.escape(e["name"]))
        if e["code"] in pages:
            name = '<a href="/articles/%s">%s</a>' % (pages[e["code"]], name)
        if e["kind"] == "權":
            cash = "配股（除權）"
        else:
            cash = "%s 元" % fmt(e["cash"]) if e["cash"] else "待公告"
        if e.get("pay"):  # 同年只寫月/日，跨年才補年份（手機版欄寬）
            pay = e["pay"].strftime("%-m/%-d" if e["pay"].year == e["ex"].year else "%Y/%-m/%-d")
        else:
            pay = "—" if e["kind"] == "權" else "待公告"
        return ('            <tr%s><td style="%s">%s</td><td style="%s">%s</td><td style="%stext-align:right;">%s</td>'
                '<td style="%s">%s</td></tr>') % (bg, S, e["ex"].strftime("%-m/%-d"), N, name, S, cash, S, pay)
    return "\n".join(row(e, i) for i, e in enumerate(events))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", help="YYYY-MM，要產生的除息月份（預設＝台灣時間本月）")
    a = ap.parse_args()
    month = a.month or (dt.datetime.utcnow() + dt.timedelta(hours=8)).strftime("%Y-%m")
    y, m = map(int, month.split("-"))
    m_start = dt.date(y, m, 1)
    m_end = (dt.date(y + (m == 12), m % 12 + 1, 1) - dt.timedelta(days=1))
    today = (dt.datetime.utcnow() + dt.timedelta(hours=8)).date()  # 台灣時間（Actions 跑在 UTC）
    pages = site_pages()
    load_holidays()

    # 行事曆收錄：近 6 個月已除息＋已預告
    ev = twse_events(min(m_start, today - dt.timedelta(days=183)), max(m_end, today + dt.timedelta(days=120)))
    codes = sorted({e["code"] for e in ev.values() if e["code"] in pages or m_start <= e["ex"] <= m_end})
    yh = {}
    for c in codes:
        try:
            yh[c] = yahoo(c)
        except Exception as ex:  # 單檔失敗不影響整體，該檔金額/發放日顯示待公告
            print("yahoo fail", c, ex)
            yh[c] = {}
        time.sleep(1)
    for e in ev.values():
        cash, pay = yh.get(e["code"], {}).get(e["ex"], (None, None))
        # 未除息的金額只認證交所公告：Yahoo 對未正式公告的配息可能顯示估計值（2026-11 00878 實例）
        if e["cash"] is None and e["kind"] != "權" and e["ex"] < today:
            e["cash"] = cash
        e["pay"] = pay
        e["slug"] = pages.get(e["code"])

    allev = sorted(ev.values(), key=lambda e: (e["ex"], e["code"]))
    with open(os.path.join(ROOT, "data", "dividend-events.json"), "w", encoding="utf-8") as fp:
        json.dump([{**e, "ex": e["ex"].isoformat(), "pay": e["pay"].isoformat() if e["pay"] else None} for e in allev],
                  fp, ensure_ascii=False, indent=1)

    os.makedirs(os.path.join(ROOT, "cal"), exist_ok=True)
    mine = [e for e in allev if e["code"] in pages]
    for c in sorted({e["code"] for e in mine}):
        open(os.path.join(ROOT, "cal", c + ".ics"), "w", encoding="utf-8", newline="").write(
            ics([e for e in mine if e["code"] == c], "%s 除息提醒｜GULICALC" % c))
    open(os.path.join(ROOT, "cal", "all.ics"), "w", encoding="utf-8", newline="").write(ics(mine, "熱門存股除息提醒｜GULICALC"))

    # 個股頁訂閱框的「下一次除息」：<!-- NEXTEX -->…<!-- /NEXTEX -->
    for c, slug in pages.items():
        p = os.path.join(ROOT, "articles", slug + ".html")
        t = open(p, encoding="utf-8").read()
        if "<!-- NEXTEX -->" not in t:
            continue
        nxt = [e for e in allev if e["code"] == c and e["ex"] >= today]
        if nxt:
            e = nxt[0]
            s = "下一次除息：%s（最後買進日 %s）" % (e["ex"].strftime("%Y/%-m/%-d"), last_buy_day(e["ex"]).strftime("%-m/%-d"))
            s += "，每股 %s 元" % fmt(e["cash"]) if e["cash"] else "，金額待公告"
            s += "，預計 %s 發放。" % e["pay"].strftime("%-m/%-d") if e.get("pay") else "。"
        else:
            s = "目前還沒有新的除息公告，公告後會自動加進行事曆。"
        t2 = re.sub(r"(<!-- NEXTEX -->).*?(<!-- /NEXTEX -->)", lambda mm: mm.group(1) + s + mm.group(2), t, flags=re.S)
        if t2 != t:
            open(p, "w", encoding="utf-8").write(t2)

    page = os.path.join(ROOT, "articles", "ex-dividend-%04d-%02d.html" % (y, m))
    if os.path.exists(page):
        month_ev = [e for e in allev if m_start <= e["ex"] <= m_end]
        t = open(page, encoding="utf-8").read()
        t, n = re.subn(r"(<!-- EVENTS:START -->).*?(<!-- EVENTS:END -->)",
                       lambda mm: mm.group(1) + "\n" + render_rows(month_ev, pages) + "\n            " + mm.group(2), t, flags=re.S)
        hot = [e for e in month_ev if e["code"] in pages]
        t, n2 = re.subn(r"(<!-- HOT:START -->).*?(<!-- HOT:END -->)",
                        lambda mm: mm.group(1) + "\n" + render_rows(hot, pages) + "\n            " + mm.group(2), t, flags=re.S)
        t = re.sub(r"(<!-- COUNT -->)[^<]*(<!-- /COUNT -->)", r"\g<1>%d\g<2>" % len(month_ev), t)
        n = n and n2
        if t != open(page, encoding="utf-8").read():  # 表格有變才更新「資料更新」日期，避免每天空 commit
            t = re.sub(r"(<!-- ASOF -->)[^<]*(<!-- /ASOF -->)", r"\g<1>%s\g<2>" % today.isoformat(), t)
        assert n == 1, "EVENTS markers missing"
        open(page, "w", encoding="utf-8").write(t)
        print("page rows:", len(month_ev))
    print("events:", len(allev), "calendars:", len({e['code'] for e in mine}))


if __name__ == "__main__":
    main()
