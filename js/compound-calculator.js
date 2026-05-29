(() => {
  const $ = (sel) => document.querySelector(sel);
  const initialInvestment = $("#initialInvestment");
  const monthlyInvestment = $("#monthlyInvestment");
  const annualYield = $("#annualYield");
  const years = $("#years");
  const totalInvestedEl = $("#totalInvested");
  const totalAssetsEl = $("#totalAssets");
  const totalDividendIncomeEl = $("#totalDividendIncome");
  const inflationRateEl = $("#inflationRate");

  function calculate() {
    const initial = Math.max(0, parseFloat(initialInvestment.value) || 0);
    const monthly = Math.max(0, parseFloat(monthlyInvestment.value) || 0);
    const rate = Math.max(0, Math.min(parseFloat(annualYield.value) || 0, 50));
    const numYears = Math.max(0, Math.min(parseFloat(years.value) || 0, 100));
    const inflation = Math.max(0, parseFloat(inflationRateEl?.value) || 0);

    const totalInvested = initial + monthly * 12 * numYears;

    // Compound monthly: each month apply monthly yield then add contribution
    const monthlyRate = rate / 12 / 100;
    const totalMonths = Math.floor(numYears * 12);
    let assets = initial;

    for (let m = 0; m < totalMonths; m++) {
      assets = assets * (1 + monthlyRate) + monthly;
    }

    const totalDividendIncome = assets - totalInvested;

    totalInvestedEl.textContent = Math.round(totalInvested).toLocaleString("zh-TW");
    totalAssetsEl.textContent = Math.round(assets).toLocaleString("zh-TW");
    totalDividendIncomeEl.textContent = Math.round(totalDividendIncome).toLocaleString("zh-TW");

    // Inflation adjustment
    const inflationNote = document.getElementById('inflationNote');
    if (inflationNote && inflation > 0 && numYears > 0 && assets > 0) {
      const realAssets = assets / Math.pow(1 + inflation / 100, numYears);
      document.getElementById('inflationPct').textContent = inflation;
      document.getElementById('realAssets').textContent = Math.round(realAssets).toLocaleString("zh-TW");
      inflationNote.style.display = 'block';
    } else if (inflationNote) {
      inflationNote.style.display = 'none';
    }

    // Draw growth chart
    const wrap = document.getElementById('compoundChartWrap');
    if (numYears > 0 && (initial > 0 || monthly > 0) && typeof Chart !== 'undefined') {
      wrap.style.display = 'block';
      const labels = [];
      const investedData = [];
      const assetsData = [];
      let a = initial;
      for (let y = 0; y <= numYears; y++) {
        labels.push(y + '年');
        investedData.push(Math.round(initial + monthly * 12 * y));
        assetsData.push(Math.round(a));
        for (let m = 0; m < 12; m++) { a = a * (1 + monthlyRate) + monthly; }
      }
      if (window._compChart) window._compChart.destroy();
      window._compChart = new Chart(document.getElementById('compoundChart'), {
        type: 'line',
        data: {
          labels: labels,
          datasets: [
            { label: '總投入', data: investedData, borderColor: '#9ca3af', backgroundColor: 'rgba(156,163,175,0.1)', fill: true, tension: 0.3, pointRadius: 0 },
            { label: '預估總資產', data: assetsData, borderColor: '#0891b2', backgroundColor: 'rgba(8,145,178,0.15)', fill: true, tension: 0.3, pointRadius: 0 }
          ]
        },
        options: {
          responsive: true,
          plugins: { legend: { position: 'bottom', labels: { font: { size: 12 }, padding: 12 } } },
          scales: {
            y: { ticks: { callback: v => (v >= 10000 ? (v/10000).toFixed(0) + '萬' : v) } }
          }
        }
      });
    } else if (wrap) { wrap.style.display = 'none'; }
  }

  [initialInvestment, monthlyInvestment, annualYield, years, inflationRateEl].filter(Boolean).forEach((input) => {
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
