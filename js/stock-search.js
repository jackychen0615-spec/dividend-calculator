/* 可重用的個股搜尋帶入：用 #stockSearch + #stockDropdown，
   透過 data-target-price / data-target-dividend 指定要帶入的欄位。
   資料來源同首頁：合併即時 TWSE API 與 stocks.json（含 ETF）。 */
(function () {
  var input = document.getElementById("stockSearch");
  var dropdown = document.getElementById("stockDropdown");
  var wrap = document.getElementById("stockSearchWrap");
  if (!input || !dropdown) return;

  var priceSel = input.getAttribute("data-target-price");
  var divSel = input.getAttribute("data-target-dividend");
  var stocksData = [];
  var debounceTimer = null;

  function mergeStocks(live, stat) {
    var map = {};
    stat.forEach(function (s) { map[s.code] = s; });
    live.forEach(function (s) {
      var ex = map[s.code];
      if (ex) {
        if (s.price) ex.price = s.price;
        if (s.dividend != null) ex.dividend = s.dividend;
        if (s.dividendYield != null) ex.dividendYield = s.dividendYield;
      } else {
        // 收錄所有股票（含新 ETF 尚無配息者）；沒配息的照樣可搜尋、帶入股價
        map[s.code] = s;
      }
    });
    return Object.keys(map).map(function (k) { return map[k]; });
  }

  Promise.all([
    fetch("/api/stocks").then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; }),
    fetch("/data/stocks.json").then(function (r) { return r.ok ? r.json() : null; }).catch(function () { return null; })
  ]).then(function (res) {
    var live = (res[0] && res[0].stocks) ? res[0].stocks : [];
    var stat = (res[1] && res[1].stocks) ? res[1].stocks : [];
    stocksData = mergeStocks(live, stat);
  });

  function fuzzyMatch(q, s) {
    q = q.toLowerCase();
    return s.code.toLowerCase().indexOf(q) !== -1 || (s.name || "").toLowerCase().indexOf(q) !== -1;
  }

  function setField(sel, val) {
    if (!sel) return;
    var el = document.querySelector(sel);
    if (!el) return;
    el.value = val;
    el.dispatchEvent(new Event("input", { bubbles: true }));
  }

  function selectStock(s) {
    setField(priceSel, s.price);
    // 沒配息資料就不覆蓋股利欄，留給使用者自行輸入
    if (s.dividend != null && s.dividend !== "") setField(divSel, s.dividend);
    input.value = "";
    dropdown.style.display = "none";
  }

  function render(results) {
    if (!results.length) { dropdown.style.display = "none"; return; }
    var html = "";
    results.forEach(function (s, i) {
      var hasDiv = s.dividend != null && s.dividend !== "";
      var y = hasDiv ? (s.dividendYield || (s.price > 0 ? (s.dividend / s.price * 100).toFixed(2) : "0")) : null;
      if (typeof y === "number") y = y.toFixed(2);
      var freq = s.frequency ? s.frequency + " | " : "";
      var right = hasDiv ? '<span style="font-size:.75rem;color:#0891b2;font-weight:600;">殖利率 ' + y + '%</span>'
                         : '<span style="font-size:.72rem;color:#9ca3af;">配息待更新</span>';
      var bottom = hasDiv ? (freq + '股價 ' + s.price + ' 元 | 配息 ' + s.dividend + ' 元')
                          : ('股價 ' + s.price + ' 元 | 配息資料待更新，帶入後請自行輸入');
      html += '<li data-idx="' + i + '" style="padding:.6rem .8rem;cursor:pointer;border-bottom:1px solid #f3f4f6;">'
        + '<div style="display:flex;justify-content:space-between;align-items:center;">'
        + '<div><strong style="color:#1f2937;font-size:.9rem;">' + s.code + '</strong> <span style="color:#6b7280;font-size:.82rem;">' + s.name + '</span></div>'
        + right + '</div>'
        + '<div style="font-size:.72rem;color:#9ca3af;margin-top:.15rem;">' + bottom + '</div></li>';
    });
    dropdown.innerHTML = html;
    dropdown.style.display = "block";
    dropdown.querySelectorAll("li").forEach(function (li) {
      li.addEventListener("click", function () { selectStock(results[parseInt(this.getAttribute("data-idx"))]); });
    });
  }

  input.addEventListener("input", function () {
    var val = this.value.trim();
    clearTimeout(debounceTimer);
    if (!val) { dropdown.style.display = "none"; return; }
    debounceTimer = setTimeout(function () {
      render(stocksData.filter(function (s) { return fuzzyMatch(val, s); }).slice(0, 8));
    }, 200);
  });

  document.addEventListener("click", function (e) {
    if (wrap && !wrap.contains(e.target)) dropdown.style.display = "none";
  });
})();
