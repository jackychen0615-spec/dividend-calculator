# GULICALC.com — SEO/AEO/GEO Action Plan
依優先順序排列，對應 [FULL-AUDIT-REPORT.md](./FULL-AUDIT-REPORT.md) 的發現。

## 🔴 立即（今天可做完，零風險）

- [ ] **移除/改寫 FAQPage schema**（`index.html`、`ex-dividend-calculator.html`）
  - 把 `"@type": "FAQPage"` 的 JSON-LD 區塊拿掉
  - 底下的 Q&A 文字內容保留在頁面上（使用者看得到就好，不用 schema 包裝）
  - 已有的 `speakable` schema 不受影響，繼續保留
  - 驗證方式：改完後跑 `python3 /Users/jackychen/.claude/skills/Agentic-SEO-Skill/scripts/validate_schema.py <file>` 確認警告消失

- [ ] **修正 about.html 的 `<title>`**
  - 現在：`關於我們 - 股利計算器`
  - 建議改成：`關於 GULICALC｜台股存股工具開發者 Jacky Chen 的故事 - 股利計算器`（或類似、補上關鍵字+可信度訊號的版本）

## ⚠️ 1個月內（可分批做，跟既有 Task #4「連結建設」合併執行）

- [ ] **回填 orphan pages 的站內連結**（75篇候選，見完整清單於 audit report）
  - 不用一次做完，建議每次寫新文章時，順手往 2-3 篇相關舊文章加連結
  - 優先處理同主題群組（例如：金融股系列互相連結、ETF系列互相連結）
  - 可以在既有的「延伸閱讀」區塊模式基礎上擴充（`dividend-investor-book-list.html` 已有範例可複製）

- [ ] **補 Twitter Card 選填欄位**（低優先，錦上添花）
  - 加 `<meta name="twitter:site" content="@你的帳號">`（如果有經營 Twitter/X 帳號的話，沒有就跳過這項）

## ℹ️ 需要額外資源才能驗證（非本次可完成）

- [ ] **重跑 Core Web Vitals 檢測**：申請免費 PageSpeed Insights API key，或手動用 https://pagespeed.web.dev/ 測首頁、`/ex-dividend-calculator`、任一篇文章頁，補齊本次因限流而缺少的 LCP/INP/CLS 數據

## ✅ 不用做（已驗證沒問題，避免過度優化）

- 個股模板文章的重複內容風險：已人工驗證僅 16.6% 結構重疊，不是 duplicate content，Path B 深化內容的做法可以繼續
- robots.txt / llms.txt / 安全性標頭 / 壞連結 / alt 屬性：全部已達標，不用碰
