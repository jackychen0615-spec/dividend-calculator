(() => {
  const $ = (sel) => document.querySelector(sel);
  const monthlyAmount = $("#monthlyAmount");
  const annualReturn = $("#annualReturn");
  const investYears = $("#investYears");
  const totalInputEl = $("#totalInput");
  const totalValueEl = $("#totalValue");
  const totalReturnEl = $("#totalReturn");

  function calculate() {
    const monthly = parseFloat(monthlyAmount.value) || 0;
    const rate = parseFloat(annualReturn.value) || 0;
    const years = parseFloat(investYears.value) || 0;

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
  }

  [monthlyAmount, annualReturn, investYears].forEach((input) => {
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
