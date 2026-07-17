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

## ⚠️ 新發現（處理內鏈時順便發現，已全部處理）

- [x] **`sitemap.xml` 缺少 28 篇文章**（2026-07-17 已修）：本機 `articles/` 資料夾實際有 120 個檔案，`sitemap.xml` 原本只登記 92 篇。缺漏的是「vs比較頁」（如 `0050-vs-006208`）與週報/月報系列（`weekly-report-2026-w24` 等）。已補上全部 28 篇，`lastmod` 取自各文章頁面顯示的更新日期，`priority` 統一 0.8（跟同類文章一致）。XML 驗證通過，現在 120 篇文章 100% 都在 sitemap 裡。
- [x] **6 篇文章補上「延伸閱讀」outbound 區塊**（2026-07-18 已修）：`dividend-calculation-examples`、`dividend-yield-explained`、`ex-dividend-date-guide`、`high-dividend-yield-stocks`、`how-much-dividend-per-share`、`taiwan-stock-dividend-guide` 各補 4 條主題相關連結，格式與其他文章一致（`<h3>延伸閱讀</h3>` + `<ul>`），位置放在資料來源/免責聲明段落之後、`</article>` 之前。結構驗證通過。

## 補選填（低優先，錦上添花）

- [x] ~~補 Twitter Card 選填欄位~~：站長確認沒有經營 X/Twitter 帳號，跳過此項（不影響 SEO）

## ℹ️ 環境限制（已嘗試修復，暫時卡住，非站點問題）

- [ ] **Core Web Vitals 檢測持續失敗**：API 路徑（`pagespeed.py`）與網頁版（pagespeed.web.dev）都試過，兩者皆卡在限流/無回應超過 1 分鐘，非本站問題。建議之後手動申請免費 PageSpeed Insights API key（Google Cloud Console）再重跑，或等一段時間後直接用 https://pagespeed.web.dev/ 重試。

## ✅ 不用做（已驗證沒問題，避免過度優化）

- 個股模板文章的重複內容風險：已人工驗證僅 16.6% 結構重疊，不是 duplicate content，Path B 深化內容的做法可以繼續
- robots.txt / llms.txt / 安全性標頭 / 壞連結 / alt 屬性：全部已達標，不用碰
