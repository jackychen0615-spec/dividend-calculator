/**
 * ETF 頁即時更新：抓 /api/etf-dividends，把計算器帶入值與殖利率換成現價即時值。
 * 頁面需先設定 window.ETF_CODE = "0056"。
 * 失敗時靜默略過，頁面沿用寫死的靜態值（不影響顯示）。
 * 也會更新任何 [data-etf="price|yield|dividend"] 元素的文字。
 */
(function () {
  var code = window.ETF_CODE;
  if (!code) return;

  fetch("/api/etf-dividends")
    .then(function (r) { return r.json(); })
    .then(function (j) {
      var d = j && j.data && j.data[code];
      if (!d || !d.price) return;

      // 更新計算器 widget（若存在）
      var p = document.getElementById("gcP");
      var dv = document.getElementById("gcD");
      if (p && dv) {
        p.value = d.price;
        dv.value = d.dividend;
        // 觸發 widget 內建 calc() 重算 gcY/gcC/gcT
        p.dispatchEvent(new Event("input", { bubbles: true }));
      }

      // 更新標註元素（可選）
      document.querySelectorAll('[data-etf="price"]').forEach(function (el) { el.textContent = d.price; });
      document.querySelectorAll('[data-etf="yield"]').forEach(function (el) { el.textContent = d.yield; });
      document.querySelectorAll('[data-etf="dividend"]').forEach(function (el) { el.textContent = d.dividend; });
    })
    .catch(function () { /* 靜默：沿用靜態值 */ });
})();
