(() => {
  const $ = (sel) => document.querySelector(sel);
  const stockPrice = $("#stockPrice");
  const shares = $("#shares");
  const dividend = $("#dividend");
  const totalCostEl = $("#totalCost");
  const totalDividendEl = $("#totalDividend");
  const yieldRateEl = $("#yieldRate");

  function calculate() {
    const price = Math.max(0, parseFloat(stockPrice.value) || 0);
    const shareCount = Math.max(0, Math.min(parseFloat(shares.value) || 0, 99999999));
    const div = Math.max(0, parseFloat(dividend.value) || 0);

    const totalCost = shareCount * price;
    const totalDividend = shareCount * div;
    const yieldRate = price > 0 ? (div / price) * 100 : 0;

    totalCostEl.textContent = totalCost.toLocaleString("zh-TW", {
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    });
    totalDividendEl.textContent = totalDividend.toLocaleString("zh-TW", {
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    });
    yieldRateEl.textContent = yieldRate.toFixed(2);

    // Yield rate gauge
    const gauge = document.getElementById('yieldGauge');
    if (yieldRate > 0 && gauge) {
      gauge.style.display = 'block';
      const pct = Math.min(yieldRate / 12 * 100, 100);
      document.getElementById('yieldPointer').style.left = 'calc(' + pct + '% - 2px)';
      let level = '偏低';
      let color = '#9ca3af';
      if (yieldRate >= 7) { level = '高殖利率'; color = '#dc2626'; }
      else if (yieldRate >= 5) { level = '中高殖利率'; color = '#0891b2'; }
      else if (yieldRate >= 3) { level = '中等殖利率'; color = '#10b981'; }
      document.getElementById('yieldLabel').innerHTML = '你的殖利率 <strong style="color:' + color + ';font-size:1.1rem;">' + yieldRate.toFixed(2) + '%</strong> — ' + level;
    } else if (gauge) {
      gauge.style.display = 'none';
    }
  }

  [stockPrice, shares, dividend].forEach((input) => {
    input.addEventListener("input", calculate);
  });

  // FAQ accordion
  document.querySelectorAll(".faq-question").forEach((btn) => {
    btn.addEventListener("click", () => {
      const item = btn.parentElement;
      item.classList.toggle("open");
    });
  });

  // Mobile nav toggle
  const toggle = $(".nav-toggle");
  const navLinks = $(".nav-links");
  if (toggle && navLinks) {
    toggle.addEventListener("click", () => {
      navLinks.classList.toggle("open");
    });
  }
})();
