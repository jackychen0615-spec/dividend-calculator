# GULICALC.com — 技術SEO / AEO / GEO / E-E-A-T Audit Report
**日期**: 2026-07-17　**範圍**: 全站（首頁、10個計算工具、100+ 篇文章）　**方法**: Agentic-SEO-Skill（腳本驗證 + LLM 推理）

**背景**：本站正在爭取 Google AdSense 審核通過，此次 audit 聚焦「內容品質」「技術健康度」「AI 可發現性」等 Google 會評估的訊號，而非單純排名優化。

---

## 總分：78/100（Good）

| 類別 | 權重 | 分數 | 備註 |
|---|---|---|---|
| 技術 SEO | 25% | 90 | robots.txt / security headers / 無壞連結，全部滿分 |
| 內容品質 | 20% | 70 | 內容量充足，但 orphan pages 偏多 |
| On-Page SEO | 15% | 75 | 多數頁面 title/meta 完整，about 頁 title 過弱 |
| Schema / 結構化資料 | 15% | 55 | **FAQPage 誤用是本次最大扣分項** |
| Performance (CWV) | 10% | N/A | 環境限制，PageSpeed API 被限流，未取得數據 |
| 圖片優化 | 10% | 95 | 檢查頁面均無缺 alt |
| AI 搜尋就緒度 (GEO) | 5% | 95 | llms.txt 100分、AI crawler 全開放 |

---

## 🔴 Critical（立即修正）

### 1. FAQPage schema 誤用（首頁 + 除權息計算機頁）
**證據**：`validate_schema.py` 明確警告：
```
Block 1: @type 'FAQPage' is restricted to government and healthcare sites only (Aug 2023) — verify site qualifies
```
確認出現在 `index.html` 和 `ex-dividend-calculator.html` 的 JSON-LD 中。

**影響**：Google 自 2023 年 8 月起，FAQPage 富結果（搜尋結果下方展開的問答）**只保留給政府與醫療權威網站**。商業網站（本站屬於此類）掛 FAQPage schema：
- 不會顯示富結果，等於白掛
- 技術上算「結構化資料使用不當」，長期可能被 Search Console 標記為 schema 問題（雖不至於手動處置，但也是雜訊）
- 不影響 AdSense 審核本身，但清理它是低成本、零風險的加分項

**修正**：把這兩頁的 `"@type": "FAQPage"` 區塊改成一般的 `Question`/`Answer` 純文字內容（不用 schema 包裝），或改用你已經在用的 `WebPage` + `speakable` 就好。**不要**用其他方式偽裝繼續掛 FAQ 富結果 schema。

---

## ⚠️ Warning（1個月內修正）

### 2. 75 個潛在孤兒頁面（Orphan Pages）
**證據**：`internal_links.py` 爬取 21 個入口頁、發現 125 個不重複網址，其中 **75 個只有 1 個站內連結指向**（幾乎都只從 `/articles` 文章列表頁被連到一次），例如：
- `/articles/how-much-dividend-per-share`
- `/articles/dividend-payment-schedule`
- `/articles/total-return-vs-yield-2026`
- `/articles/stock-saving-outlook-h2-2026`
等 75 篇。

**影響**：站內連結權重（internal link equity）幾乎沒有從其他相關文章流向這些頁面，等於每篇文章都在孤島上，不利於：
- Google 判斷內容之間的主題關聯（topical authority）
- 使用者/AI 爬蟲從一篇文章自然發現相關文章（GEO 訊號之一）

**修正**：不需要一次做完，但建議：
1. 每篇新文章結尾的「延伸閱讀」區塊（你在 `dividend-investor-book-list.html` 已經有做這個），往舊文章回填 2-3 個相關連結
2. 優先處理主題相近的文章群（例如同樣講金融股的文章互相連結）
3. 不用急著全部 75 篇都補，抓「同主題群組」批次處理最有效率

### 3. about 頁 title tag 過弱
**證據**：`<title>` 目前是「關於我們 - 股利計算器」（僅 12 字），對比其他頁面如首頁「股利計算器｜一秒算出殖利率和股利 - 免費線上試算工具 GULICALC」（36字，關鍵字豐富），about 頁明顯沒有跟上同樣的命名規則。
**修正**：改成類似「關於 GULICALC｜台股存股工具開發者 Jacky Chen 的故事 - 股利計算器」，補上關鍵字與可信度訊號（對 E-E-A-T 的 Authoritativeness 也有幫助）。

---

## ✅ Pass（已達標，不用動）

| 項目 | 結果 |
|---|---|
| robots.txt | 15 個 User-Agent 規則齊全，GPTBot/ClaudeBot/PerplexityBot/Google-Extended/Applebot-Extended 等全部明確允許（滿分） |
| llms.txt | 存在，7 個區塊、23 個連結，品質分數 **100/100** |
| 安全性標頭 | HTTPS + HSTS + CSP + X-Frame-Options + X-Content-Type-Options + Referrer-Policy + Permissions-Policy，安全分數 **100/100** |
| 壞連結 | 抽測 30 條連結，0 個壞連結、0 個逾時 |
| 圖片 alt | 首頁/工具頁/文章頁/about頁抽測皆無缺 alt |
| Open Graph / Twitter Card | 85/100，OG 標籤 7/7 齊全，僅缺選填的 twitter:site/twitter:creator |
| Schema 覆蓋率 | 首頁有 WebApplication/WebSite，文章頁有 Article+BreadcrumbList，about 頁有 Organization+ProfilePage，均為正確、非過時的 schema 類型 |
| 模板化個股文章的重複內容風險 | 手動比對「華南金」vs「開發金」兩篇同模板文章，char-level 6-gram Jaccard 相似度僅 **16.6%**（多為公式/標籤等正常結構重疊），**不構成 duplicate content 風險**——Path B（深化金融垂直內容）目前執行方式是安全的 |
| INP/FID | 全站掃描頁面均未發現已淘汰的 FID 引用 |

---

## ℹ️ 環境限制（Environment Limitations，非站點問題）

1. **PageSpeed/Core Web Vitals**：Google PageSpeed Insights API 未設定 API key，被限流（`Rate limited by API`），本次未取得 LCP/INP/CLS 實測數據。建議之後手動跑 https://pagespeed.web.dev/ 或申請免費 API key 重跑。
2. **readability.py 對中文內容誤判**：此腳本用英文語系的音節/句子切分邏輯，對繁體中文文章會誤判成「3個字」「內容過短」——這是腳本本身不支援 CJK，**不是真的內容過短**（人工確認文章頁實際約 1500-2200+ 字）。已用人工方式重新確認字數，排除此為假訊號。
3. **duplicate_content.py 自動爬蟲**：腳本回傳「爬到 0 頁」（工具本身的爬蟲邏輯問題），已改用人工抽樣比對兩篇模板文章替代驗證（見上方 Pass 項目）。

---

## E-E-A-T 現況評估（依 Google 2025年12月核心更新標準）

| 面向 | 現況 | 評分 |
|---|---|---|
| Experience（經驗，權重20%） | about 頁有創辦人第一人稱故事，但**缺少具體「操作過程」的第一手證據**（如截圖、實際存股紀錄畫面） | Moderate |
| Expertise（專業，權重25%） | 有作者身分（Jacky Chen，人資背景轉行）、公式透明化，但作者本身非金融專業背景是雙面刃——建議持續強調「工具透明公式」而非「投資建議」定位 | Moderate |
| Authoritativeness（權威性，權重25%） | 有 GitHub/Medium/Portfolio 連結佐證身分真實性，但缺少外部引用/媒體報導 | Weak-Moderate |
| Trustworthiness（信任度，權重30%，最重要） | HTTPS✅、隱私權政策✅、使用條款✅、免責聲明清楚✅、聯絡頁✅、不收集個資的說明✅ | **Strong** |

**綜合**：Trustworthiness 這個佔比最高的面向已經做得不錯，這對 AdSense 審核是加分的（AdSense 也很看重「網站是否透明、是否清楚說明自己是誰」）。真正的弱項是 Experience 與 Authoritativeness——如果之後想再進一步強化，方向是「放創辦人實際存股畫面截圖」「爭取被財經媒體或部落格引用」，但這屬於長期建設，非本次 audit 的緊急項。

---

## 與 AdSense 審核的關聯性小結

這次 audit 沒有發現任何「low value content」「政策違規」等會直接導致 AdSense 拒絕的紅旗訊號。網站的技術基礎（安全性、robots.txt、llms.txt、無壞連結）其實已經優於一般個人站水準。真正值得處理的是：
1. FAQPage schema 誤用（小成本、零風險，建議先修）
2. Orphan pages 偏多（中期，跟你之前定的「Month 3：連結建設」任務可以合併處理）
3. about 頁 title 太弱（5分鐘可以改完）

這些都不是「內容太爛」的訊號，反而更多是可以快速補強的技術細節。
