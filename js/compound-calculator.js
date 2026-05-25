(() => {
  const $ = (sel) => document.querySelector(sel);
  const initialInvestment = $("#initialInvestment");
  const monthlyInvestment = $("#monthlyInvestment");
  const annualYield = $("#annualYield");
  const years = $("#years");
  const totalInvestedEl = $("#totalInvested");
  const totalAssetsEl = $("#totalAssets");
  const totalDividendIncomeEl = $("#totalDividendIncome");

  function calculate() {
    const initial = Math.max(0, parseFloat(initialInvestment.value) || 0);
    const monthly = Math.max(0, parseFloat(monthlyInvestment.value) || 0);
    const rate = Math.max(0, Math.min(parseFloat(annualYield.value) || 0, 50));
    const numYears = Math.max(0, Math.min(parseFloat(years.value) || 0, 100));

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
  }

  [initialInvestment, monthlyInvestment, annualYield, years].forEach((input) => {
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
