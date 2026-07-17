// 除權息參考價試算 — 公式來源：台灣證券交易所官方公式
// 除權息參考價 = (除權息前股價 − 現金股利) / (1 + 股票股利/10)
// https://www.twse.com.tw/zh/announcement/ex-right/cal.html
(function () {
  var exPrice = document.getElementById('exPrice');
  var cashDividend = document.getElementById('cashDividend');
  var stockDividend = document.getElementById('stockDividend');
  if (!exPrice || !cashDividend || !stockDividend) return;

  function fmt(n, d) {
    d = d || 0;
    return Number(n).toLocaleString('zh-TW', { minimumFractionDigits: d, maximumFractionDigits: d });
  }

  function calc() {
    var price = Math.max(0, parseFloat(exPrice.value) || 0);
    var cash = Math.max(0, parseFloat(cashDividend.value) || 0);
    var stock = Math.max(0, parseFloat(stockDividend.value) || 0);

    var allotRate = stock / 10; // 無償配股率：股票股利(元) ÷ 面額10元
    var refPrice = price > 0 ? (price - cash) / (1 + allotRate) : 0;
    var dropAmount = price - refPrice;
    var dropPct = price > 0 ? (dropAmount / price) * 100 : 0;
    var cashYield = price > 0 ? (cash / price) * 100 : 0;

    document.getElementById('refPrice').textContent = fmt(refPrice, 2);
    document.getElementById('dropAmount').textContent = fmt(dropAmount, 2);
    document.getElementById('dropPct').textContent = fmt(dropPct, 2);
    document.getElementById('cashYieldOut').textContent = fmt(cashYield, 2);

    var stockRow = document.getElementById('stockAllotRow');
    if (stockRow) {
      if (stock > 0) {
        stockRow.style.display = '';
        var extraShares = Math.round(allotRate * 1000); // 每張(1000股)可增配股數
        document.getElementById('extraShares').textContent = fmt(extraShares, 0);
      } else {
        stockRow.style.display = 'none';
      }
    }
  }

  [exPrice, cashDividend, stockDividend].forEach(function (el) {
    el.addEventListener('input', calc);
  });
  calc();
})();
