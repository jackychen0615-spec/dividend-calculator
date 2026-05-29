(() => {
  const $ = (sel) => document.querySelector(sel);
  const monthlyAmount = $("#monthlyAmount");
  const annualReturn = $("#annualReturn");
  const investYears = $("#investYears");
  const totalInputEl = $("#totalInput");
  const totalValueEl = $("#totalValue");
  const totalReturnEl = $("#totalReturn");

  function calculate() {
    const monthly = Math.max(0, parseFloat(monthlyAmount.value) || 0);
    const rate = Math.max(0, Math.min(parseFloat(annualReturn.value) || 0, 50));
    const years = Math.max(0, Math.min(parseFloat(investYears.value) || 0, 100));

    const totalInput = monthly * 12 * years;
    const monthlyRate = rate / 100 / 12;
    const totalMonths = Math.floor(years * 12);

    let totalValue;
    if (monthlyRate === 0) {
      totalValue = totalInput;
    } else {
      totalValue =
        monthly *
        ((Math.pow(1 + monthlyRate, totalMonths) - 1) / monthlyRate) *
        (1 + monthlyRate);
    }

    const totalReturn = totalValue - totalInput;

    const fmt = (n) =>
      Math.round(n).toLocaleString("zh-TW", { maximumFractionDigits: 0 });

    totalInputEl.textContent = fmt(totalInput);
    totalValueEl.textContent = fmt(totalValue);
    totalReturnEl.textContent = fmt(totalReturn);

    // Inflation adjustment
    const dcaInflEl = document.getElementById('dcaInflation');
    const dcaInflNote = document.getElementById('dcaInflationNote');
    const inflation = Math.max(0, parseFloat(dcaInflEl?.value) || 0);
    if (dcaInflNote && inflation > 0 && years > 0 && totalValue > 0) {
      const realValue = totalValue / Math.pow(1 + inflation / 100, years);
      document.getElementById('dcaInflPct').textContent = inflation;
      document.getElementById('dcaRealAssets').textContent = fmt(realValue);
      dcaInflNote.style.display = 'block';
    } else if (dcaInflNote) {
      dcaInflNote.style.display = 'none';
    }

    // Draw growth chart
    const wrap = document.getElementById('dcaChartWrap');
    if (years > 0 && monthly > 0 && typeof Chart !== 'undefined') {
      wrap.style.display = 'block';
      const labels = [];
      const investedData = [];
      const valueData = [];
      for (let y = 0; y <= years; y++) {
        labels.push(y + '年');
        investedData.push(Math.round(monthly * 12 * y));
        const n = y * 12;
        let v;
        if (monthlyRate === 0) { v = monthly * n; }
        else { v = monthly * ((Math.pow(1 + monthlyRate, n) - 1) / monthlyRate) * (1 + monthlyRate); }
        valueData.push(Math.round(v));
      }
      if (window._dcaChart) window._dcaChart.destroy();
      window._dcaChart = new Chart(document.getElementById('dcaChart'), {
        type: 'line',
        data: {
          labels: labels,
          datasets: [
            { label: '總投入', data: investedData, borderColor: '#9ca3af', backgroundColor: 'rgba(156,163,175,0.1)', fill: true, tension: 0.3, pointRadius: 0 },
            { label: '預估總資產', data: valueData, borderColor: '#0891b2', backgroundColor: 'rgba(8,145,178,0.15)', fill: true, tension: 0.3, pointRadius: 0 }
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

  const dcaInflInput = document.getElementById('dcaInflation');
  [monthlyAmount, annualReturn, investYears, dcaInflInput].filter(Boolean).forEach((input) => {
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
