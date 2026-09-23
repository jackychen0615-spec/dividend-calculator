/**
 * Phase 5A — Universal Live Price Layer
 *
 * 全 42 頁 ETF/股票計算頁共用的即時股價層。讀取每頁自己的
 * window.GULICALC_PAGE_DATA.symbol，向 /api/stocks（production 涵蓋
 * ~1200+ 檔台股/ETF 的即時或收盤價 Cloudflare Function）查詢最新市場價格。
 *
 * 資料優先序：
 *   /api/stocks live price  →  GULICALC_PAGE_DATA.price（人工核准 static
 *   snapshot）fallback。API 失敗、查無該 symbol、或價格無效時，什麼都不做，
 *   頁面維持原本寫死的核准值——不清空、不覆寫成 null。
 *
 * 只允許覆寫：
 *   - #gcP（股價計算器 input）的 value
 *   - 透過對 #gcP 觸發 "input" 事件，交給頁面既有的 calc() 函式重算
 *     gcY（殖利率顯示）/gcC（市值）/gcT（股利試算）/qaPrice/qaYield ——
 *     這些本來就是每頁自己既有的、由使用者輸入驅動的重算邏輯，本層只是
 *     用即時股價取代原本使用者手動輸入的角色，不新增第二套計算邏輯。
 *
 * 絕對不覆寫：
 *   #gcD（配息 input，calc() 讀這個算殖利率，本層完全不碰，dividend 永遠
 *   維持頁面核准的 static 值）、dividendAmount/annualDividend/
 *   dividendBasis/distributionEvents/stockDividendParValuePerShare、
 *   任何 prose／FAQ／meta／JSON-LD、以及 GULICALC_PAGE_DATA 裡除了透過
 *   calc() 自然更新的 price/yield 之外的任何欄位。
 *
 * 不改寫既有的「資料時間・資料來源」句子本身（那是人工核准的引用文字，
 * 42 頁各自手寫、格式不完全一致，regex 硬改風險高）；改用「附加」的方式，
 * 在後面加一段小字說明已用最新股價更新，不宣稱「即時」（/api/stocks 只有
 * 批次層級的 lastUpdated，不是每檔股票的個別時間戳，不足以宣稱即時）。
 *
 * API 失敗、找不到 symbol、或找不到 #gcP：靜默略過，不做任何 DOM 變更，
 * 頁面完全等同於這支腳本不存在——這正是「API失敗→使用頁面參考股價」的
 * fallback 行為，不需要額外程式碼去「還原」，因為本來就沒有覆寫。
 */
(function () {
  var PD = window.GULICALC_PAGE_DATA;
  if (!PD || !PD.symbol) return;

  var p = document.getElementById("gcP");
  if (!p) return;

  // Phase 5A micro revision：改用 symbol-scoped query（/api/stocks?code=X），
  // 只下載這頁需要的單一標的，不再抓整包 1200+ 檔（gzip 前 214KB / 後
  // 39KB）。functions/api/stocks.js 對 ?code= 做了 backward-compatible
  // 擴充：查無此參數時回應與之前完全一樣，不影響首頁/search 的 full fetch。
  fetch("/api/stocks?code=" + encodeURIComponent(PD.symbol))
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (j) {
      if (!j || !Array.isArray(j.stocks)) return;
      var s = j.stocks[0]; // server 已篩選成單一標的，這裡只需取第一筆
      if (!s || s.code !== PD.symbol || !s.price || s.price <= 0) return; // 找不到或無效：靜默，維持既有值

      p.value = s.price;
      p.dispatchEvent(new Event("input", { bubbles: true }));

      var src = document.getElementById("qaSource");
      if (src && !src.querySelector(".live-price-badge")) {
        var badge = document.createElement("span");
        badge.className = "live-price-badge";
        badge.style.cssText = "display:block;margin-top:.25rem;color:#0891b2;font-weight:600;";
        badge.textContent = "已依最新市場股價更新試算（" + s.price + " 元）";
        src.appendChild(badge);
      }

      document.dispatchEvent(new CustomEvent("gulicalc:live-price-updated", {
        detail: { symbol: PD.symbol, price: s.price }
      }));
    })
    .catch(function () { /* 靜默 fallback：不做任何 DOM 變更，頁面維持核准 static snapshot */ });
})();
