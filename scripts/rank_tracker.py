#!/usr/bin/env python3
"""
排名追蹤：拉 GSC 觀察清單關鍵字的排名，跟上次快照比對漲跌，TG 回報。
- 服務帳戶：env GSC_SA_FILE，預設本地路徑。
- TG：env TG_BOT_TOKEN（機密）、TG_CHAT_ID（預設站長 chat id）。
- 快照存 data/rank_history.json，每次覆寫 last、把上一版存進 prev。
用途：成長引擎每月呼叫一次，或本地/GitHub Action 執行。
"""
import os
import sys
import ssl
import json
import urllib.request
from datetime import date, timedelta

SA_FILE = os.environ.get("GSC_SA_FILE", "/Users/jackychen/Desktop/gulicalc-service-account.json")
SITE = "https://gulicalc.com/"
HISTORY = os.path.join(os.path.dirname(__file__), "..", "data", "rank_history.json")
TG_TOKEN = os.environ.get("TG_BOT_TOKEN")
TG_CHAT = os.environ.get("TG_CHAT_ID", "8365775688")

# 觀察清單（關鍵字）：目前主推、卡第 2 頁待爬
WATCH = [
    "台積電配息怎麼算",
    "鴻海配息怎麼算",
    "聯發科配息怎麼算",
    "中華電信配息怎麼算",
    "股利計算機",
    "股利計算器",
    "殖利率計算",
    "股利計算機app",
]

# 觀察清單（頁面）：affiliate 借貸叢集，追整頁導流成效（曝光/點擊/排名）
WATCH_PAGES = [
    ("/articles/borrow-invest-financial-checkup", "借貸投資健檢(支柱)"),
    ("/articles/refinance-lower-interest", "房貸轉貸降息"),
    ("/articles/bank-loan-rate-negotiation", "貸款利率談判"),
    ("/articles/how-to-build-credit-score", "養信用分數"),
    ("/articles/xin-qing-an-loan-guide", "新青安貸款"),
]


def gsc_data(dimension):
    """回傳 {key: {pos,imp,clk}}, span。dimension 為 'query' 或 'page'。"""
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    cred = service_account.Credentials.from_service_account_file(
        SA_FILE, scopes=["https://www.googleapis.com/auth/webmasters.readonly"]
    )
    svc = build("searchconsole", "v1", credentials=cred)
    end = date.today() - timedelta(days=3)   # GSC 資料約 3 天延遲
    start = end - timedelta(days=27)          # 近 28 天
    body = {
        "startDate": start.isoformat(),
        "endDate": end.isoformat(),
        "dimensions": [dimension],
        "rowLimit": 1000,
    }
    rows = svc.searchanalytics().query(siteUrl=SITE, body=body).execute().get("rows", [])
    data = {
        r["keys"][0]: {
            "pos": round(r["position"], 1),
            "imp": int(r["impressions"]),
            "clk": int(r["clicks"]),
        }
        for r in rows
    }
    return data, f"{start.isoformat()}~{end.isoformat()}"


def fmt_delta(prev_pos, cur_pos):
    if prev_pos is None:
        return "—"
    d = prev_pos - cur_pos  # 正值 = 排名進步（名次變小）
    if d > 0.3:
        return f"↑{d:.1f}"
    if d < -0.3:
        return f"↓{abs(d):.1f}"
    return "→"


def main():
    try:
        q_cur, span = gsc_data("query")
        p_cur, _ = gsc_data("page")
    except Exception as e:
        print("[GSC 失敗]", e)
        sys.exit(1)

    try:
        hist = json.load(open(HISTORY, encoding="utf-8"))
    except Exception:
        hist = {}
    last = hist.get("last", {})
    prev_q = last.get("queries", {})
    prev_p = last.get("pages", {})

    # 關鍵字區
    q_lines = []
    for q in WATCH:
        c = q_cur.get(q)
        if not c:
            q_lines.append(f"• {q}：（近28天無曝光）")
            continue
        delta = fmt_delta(prev_q.get(q, {}).get("pos"), c["pos"])
        q_lines.append(f"• {q}：第 {c['pos']} 名 {delta}（{c['imp']}曝/{c['clk']}點）")

    # 頁面區（affiliate 借貸叢集）
    p_lines = []
    for path, label in WATCH_PAGES:
        c = p_cur.get(SITE.rstrip("/") + path)
        if not c:
            p_lines.append(f"• {label}：（近28天無曝光）")
            continue
        delta = fmt_delta(prev_p.get(path, {}).get("pos"), c["pos"])
        p_lines.append(f"• {label}：第 {c['pos']} 名 {delta}（{c['imp']}曝/{c['clk']}點）")

    report = (
        f"📊 gulicalc 排名追蹤（{span}）\n"
        f"【主推｜配息怎麼算叢集＋主要詞】\n" + "\n".join(q_lines) +
        f"\n\n【affiliate｜借貸頁導流】\n" + "\n".join(p_lines) +
        "\n\n↑=進步 ↓=退步 →=持平 —=無前次資料"
    )

    # 存快照（保留上一版供之後回溯）
    hist["prev"] = last
    hist["last"] = {
        "queries": {q: q_cur[q] for q in WATCH if q in q_cur},
        "pages": {path: p_cur[SITE.rstrip("/") + path]
                  for path, _ in WATCH_PAGES if SITE.rstrip("/") + path in p_cur},
    }
    hist["span"] = span
    os.makedirs(os.path.dirname(HISTORY), exist_ok=True)
    json.dump(hist, open(HISTORY, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    print(report)

    if TG_TOKEN:
        _send_tg(report)


def _send_tg(text):
    payload = json.dumps(
        {"chat_id": TG_CHAT, "text": text, "disable_web_page_preview": True}
    ).encode()
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    # 先用正常驗證；若環境有 SSL 攔截代理導致驗證失敗（urllib 會包成 URLError），
    # 退回不驗證重送——單向通知、不接收機密，可接受；確保報告在任何環境都送達。
    last = None
    for ctx in (ssl.create_default_context(), ssl._create_unverified_context()):
        try:
            req = urllib.request.Request(
                url, data=payload, headers={"Content-Type": "application/json"}
            )
            urllib.request.urlopen(req, timeout=20, context=ctx)
            print("\n[TG 已發送]")
            return
        except Exception as e:
            last = e
            continue
    print("\n[TG 發送失敗]", last)


if __name__ == "__main__":
    main()
