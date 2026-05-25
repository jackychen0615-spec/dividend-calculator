(function () {
  "use strict";

  // --- Calculator logic ---
  var buyPriceInput = document.getElementById("buyPrice");
  var holdSharesInput = document.getElementById("holdShares");
  var annualDividendInput = document.getElementById("annualDividend");

  var investCostEl = document.getElementById("investCost");
  var yearlyDividendEl = document.getElementById("yearlyDividend");
  var paybackYearsEl = document.getElementById("paybackYears");

  function calculate() {
    var buyPrice = Math.max(0, parseFloat(buyPriceInput.value) || 0);
    var holdShares = Math.max(0, Math.min(parseFloat(holdSharesInput.value) || 0, 99999999));
    var annualDividend = Math.max(0, parseFloat(annualDividendInput.value) || 0);

    var investCost = buyPrice * holdShares;
    var yearlyDividend = annualDividend * holdShares;
    var paybackYears = yearlyDividend > 0 ? (investCost / yearlyDividend).toFixed(1) : 0;

    investCostEl.textContent = investCost.toLocaleString("zh-TW");
    yearlyDividendEl.textContent = yearlyDividend.toLocaleString("zh-TW");
    paybackYearsEl.textContent = Number(paybackYears).toLocaleString("zh-TW");

    // Draw payback progress bar
    var wrap = document.getElementById('paybackBarWrap');
    if (yearlyDividend > 0 && investCost > 0) {
      wrap.style.display = 'block';
      var yrs = parseFloat(paybackYears);
      var maxYrs = Math.max(yrs, 30);
      var pct = Math.min((1 / yrs) * 100, 100);
      var barPct = Math.min((yrs / maxYrs) * 100, 100);
      document.getElementById('paybackBar').style.width = barPct + '%';
      document.getElementById('paybackPct').textContent = yrs + '年';
      document.getElementById('paybackEnd').textContent = Math.ceil(maxYrs) + ' 年';
      document.getElementById('paybackLabel').textContent = '每年靠股利回收 ' + (100/yrs).toFixed(1) + '% 的投入成本';
    } else if (wrap) {
      wrap.style.display = 'none';
    }
  }

  buyPriceInput.addEventListener("input", calculate);
  holdSharesInput.addEventListener("input", calculate);
  annualDividendInput.addEventListener("input", calculate);

  // --- Mobile nav toggle ---
  var navToggle = document.querySelector(".nav-toggle");
  var navLinks = document.querySelector(".nav-links");

  if (navToggle && navLinks) {
    navToggle.addEventListener("click", function () {
      navLinks.classList.toggle("open");
    });
  }

  // --- FAQ accordion ---
  var faqButtons = document.querySelectorAll(".faq-question");

  faqButtons.forEach(function (btn) {
    btn.addEventListener("click", function () {
      var item = btn.parentElement;
      var isOpen = item.classList.contains("open");

      // Close all
      document.querySelectorAll(".faq-item").forEach(function (el) {
        el.classList.remove("open");
      });

      // Toggle current
      if (!isOpen) {
        item.classList.add("open");
      }
    });
  });
})();
