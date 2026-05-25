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

    // Draw donut chart
    const wrap = document.getElementById('chartWrap');
    if (totalCost > 0 && totalDividend > 0 && typeof Chart !== 'undefined') {
      wrap.style.display = 'block';
      if (window._divChart) window._divChart.destroy();
      window._divChart = new Chart(document.getElementById('dividendChart'), {
        type: 'doughnut',
        data: {
          labels: ['投入成本', '年股利'],
          datasets: [{
            data: [totalCost, totalDividend],
            backgroundColor: ['#e5e7eb', '#0891b2'],
            borderWidth: 0
          }]
        },
        options: {
          responsive: true,
          plugins: {
            legend: { position: 'bottom', labels: { font: { size: 13 }, padding: 16 } }
          },
          cutout: '60%'
        }
      });
    } else if (wrap) {
      wrap.style.display = 'none';
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
