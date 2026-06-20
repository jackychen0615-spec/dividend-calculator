(() => {
  const $ = (sel) => document.querySelector(sel);
  const stockPrice = $("#stockPrice");
  const shares = $("#shares");
  const dividend = $("#dividend");
  const totalCostEl = $("#totalCost");
  const totalDividendEl = $("#totalDividend");
  const yieldRateEl = $("#yieldRate");

  let resultsShown = false;
  let divChart = null;

  // 持有 N 年累積領息長條圖（annual = 每年可領股利）
  function renderDividendChart(annual) {
    const wrap = document.getElementById("dividendChartWrap");
    const canvas = document.getElementById("dividendChart");
    if (!wrap || !canvas || typeof Chart === "undefined") return;
    if (!(annual > 0)) {
      wrap.style.display = "none";
      if (divChart) { divChart.destroy(); divChart = null; }
      return;
    }
    wrap.style.display = "block";
    const years = [1, 3, 5, 10, 20];
    const data = years.map((y) => Math.round(annual * y));
    if (divChart) {
      divChart.data.datasets[0].data = data;
      divChart.update();
      return;
    }
    divChart = new Chart(canvas.getContext("2d"), {
      type: "bar",
      data: {
        labels: years.map((y) => y + " 年"),
        datasets: [{
          label: "累積領息",
          data: data,
          backgroundColor: "#10b981",
          borderRadius: 6,
          maxBarThickness: 48,
        }],
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: (c) => c.parsed.y.toLocaleString("zh-TW") + " 元" } },
        },
        scales: {
          y: { beginAtZero: true, ticks: { callback: (v) => v.toLocaleString("zh-TW") } },
          x: { grid: { display: false } },
        },
      },
    });
  }

  function calculate() {
    const price = Math.max(0, parseFloat(stockPrice.value) || 0);
    const shareCount = Math.max(0, Math.min((parseFloat(shares.value) || 0) * (window.__shareUnitFactor || 1), 99999999));
    const div = Math.max(0, parseFloat(dividend.value) || 0);

    const totalCost = shareCount * price;
    const totalDividend = shareCount * div;
    const yieldRate = price > 0 ? (div / price) * 100 : 0;

    // 三個都有值才顯示結果
    const resultsEl = document.getElementById('calcResults');
    const hintEl = document.getElementById('calcHint');
    if (price > 0 && shareCount > 0 && div > 0) {
      if (!resultsShown && resultsEl) {
        resultsEl.style.maxHeight = (resultsEl.scrollHeight + 24) + 'px';
        resultsEl.style.opacity = '1';
        if (hintEl) hintEl.style.display = 'none';
        resultsShown = true;
      }
    } else if (resultsEl) {
      resultsEl.style.maxHeight = '0';
      resultsEl.style.opacity = '0';
      if (hintEl) hintEl.style.display = 'block';
      resultsShown = false;
    }

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
      let level = '偏低（成長型股票常見）';
      let color = '#9ca3af';
      if (yieldRate >= 8) { level = '極高 — 留意殖利率陷阱，確認是否因股價下跌所致'; color = '#dc2626'; }
      else if (yieldRate >= 5) { level = '高殖利率（存股族目標區間）'; color = '#0891b2'; }
      else if (yieldRate >= 3) { level = '中等（接近台股平均 3.8%）'; color = '#10b981'; }
      document.getElementById('yieldLabel').innerHTML = '你的殖利率 <strong style="color:' + color + ';font-size:1.1rem;">' + yieldRate.toFixed(2) + '%</strong><br><span style="font-size:.8rem;color:#6b7280;">' + level + '</span>';
    } else if (gauge) {
      gauge.style.display = 'none';
    }

    renderDividendChart(price > 0 && shareCount > 0 && div > 0 ? totalDividend : 0);
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
