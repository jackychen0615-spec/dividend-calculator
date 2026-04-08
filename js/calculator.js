(() => {
  const $ = (sel) => document.querySelector(sel);
  const stockPrice = $("#stockPrice");
  const shares = $("#shares");
  const dividend = $("#dividend");
  const totalSharesEl = $("#totalShares");
  const totalDividendEl = $("#totalDividend");
  const yieldRateEl = $("#yieldRate");

  function calculate() {
    const price = parseFloat(stockPrice.value) || 0;
    const lots = parseFloat(shares.value) || 0;
    const div = parseFloat(dividend.value) || 0;

    const totalShares = lots * 1000;
    const totalDividend = totalShares * div;
    const yieldRate = price > 0 ? (div / price) * 100 : 0;

    totalSharesEl.textContent = totalShares.toLocaleString("zh-TW");
    totalDividendEl.textContent = totalDividend.toLocaleString("zh-TW", {
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    });
    yieldRateEl.textContent = yieldRate.toFixed(2);
  }

  [stockPrice, shares, dividend].forEach((input) => {
    input.addEventListener("input", calculate);
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
