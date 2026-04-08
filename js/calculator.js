(() => {
  const $ = (sel) => document.querySelector(sel);
  const stockPrice = $("#stockPrice");
  const shares = $("#shares");
  const dividend = $("#dividend");
  const totalCostEl = $("#totalCost");
  const totalDividendEl = $("#totalDividend");
  const yieldRateEl = $("#yieldRate");

  function calculate() {
    const price = parseFloat(stockPrice.value) || 0;
    const shareCount = parseFloat(shares.value) || 0;
    const div = parseFloat(dividend.value) || 0;

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
