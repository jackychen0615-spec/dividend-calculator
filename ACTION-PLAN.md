# GULICALC.com — SEO/AEO/GEO Action Plan
依優先順序排列，對應 [FULL-AUDIT-REPORT.md](./FULL-AUDIT-REPORT.md) 的發現。

## ✅ 已完成（2026-07-17，commit `595ca12`，已 push 上線）

- [x] **移除 FAQPage schema**（`index.html`、`ex-dividend-calculator.html`）
  - JSON-LD 區塊已移除，`validate_schema.py` 重跑確認兩頁警告均已消失
  - 頁面上可見的 Q&A 文字內容完全沒動，只拿掉 schema 包裝

- [x] **修正 about.html 的 `<title>`**
  - 改成：`關於 GULICALC｜台股存股工具開發者 Jacky Chen 的故事 - 股利計算器`（44字）

- [x] **回填 orphan pages 的站內連結**
  - 實測發現「零文章內inbound連結」的頁面共 35 篇（比原本抓到的75篇更精確，是全站120篇文章的完整掃描結果，非抽樣）
  - 依主題分 7 群組（ETF/個股/存股策略/稅務信貸/時事/週報月報/概念教學），從 62 篇「捐贈方」文章的「延伸閱讀」區塊各補 1-2 條連結指向孤兒頁
  - 共新增 70 條站內連結，重新掃描確認 35 篇孤兒頁全部歸零
  - 所有 67 個改動檔案已跑過 HTML 標籤平衡驗證，無結構性錯誤

## ⚠️ 新發現（處理內鏈時順便發現，尚未修）

- [ ] **`sitemap.xml` 缺少約 30 篇文章**：內鏈修復過程中發現本機 `articles/` 資料夾實際有 120 個檔案，但 `sitemap.xml` 只登記了約 90 篇。缺漏的多半是「vs比較頁」（如 `0050-vs-006208`）與週報/月報系列（`weekly-report-2026-w24` 等）。這些頁面 Google 可能還沒發現，建議之後批次補進 sitemap。
- [ ] **6 篇文章完全沒有「延伸閱讀」outbound 區塊**：`dividend-calculation-examples`、`dividend-yield-explained`、`ex-dividend-date-guide`、`high-dividend-yield-stocks`、`how-much-dividend-per-share`、`taiwan-stock-dividend-guide`。這批多數本身 inbound 已經很多（是熱門引用目標），非緊急，但補上對讀者體驗與站內權重擴散仍有幫助。

## 補選填（低優先，錦上添花）

- [ ] **補 Twitter Card 選填欄位**：加 `<meta name="twitter:site" content="@你的帳號">`（如果有經營 Twitter/X 帳號的話，沒有就跳過這項）

## ℹ️ 需要額外資源才能驗證（非本次可完成）

- [ ] **重跑 Core Web Vitals 檢測**：申請免費 PageSpeed Insights API key，或手動用 https://pagespeed.web.dev/ 測首頁、`/ex-dividend-calculator`、任一篇文章頁，補齊本次因限流而缺少的 LCP/INP/CLS 數據

## ✅ 不用做（已驗證沒問題，避免過度優化）

- 個股模板文章的重複內容風險：已人工驗證僅 16.6% 結構重疊，不是 duplicate content，Path B 深化內容的做法可以繼續
- robots.txt / llms.txt / 安全性標頭 / 壞連結 / alt 屬性：全部已達標，不用碰
