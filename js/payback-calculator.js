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
    var buyPrice = parseFloat(buyPriceInput.value) || 0;
    var holdShares = parseFloat(holdSharesInput.value) || 0;
    var annualDividend = parseFloat(annualDividendInput.value) || 0;

    var investCost = buyPrice * holdShares;
    var yearlyDividend = annualDividend * holdShares;
    var paybackYears = yearlyDividend > 0 ? (investCost / yearlyDividend).toFixed(1) : 0;

    investCostEl.textContent = investCost.toLocaleString("zh-TW");
    yearlyDividendEl.textContent = yearlyDividend.toLocaleString("zh-TW");
    paybackYearsEl.textContent = Number(paybackYears).toLocaleString("zh-TW");
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
