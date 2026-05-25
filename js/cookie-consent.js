(function () {
  if (localStorage.getItem('cookie_consent')) return;

  var banner = document.createElement('div');
  banner.id = 'cookie-banner';
  banner.innerHTML =
    '<div class="cookie-content">' +
    '<p>本網站使用 Cookie 提供廣告服務（Google AdSense）及流量分析，繼續使用即表示您同意我們的 <a href="/privacy.html">隱私權政策</a>。</p>' +
    '<div class="cookie-actions">' +
    '<button id="cookie-accept" class="cookie-btn-accept">接受所有 Cookie</button>' +
    '<button id="cookie-reject" class="cookie-btn-reject">僅接受必要項目</button>' +
    '</div>' +
    '</div>';

  var style = document.createElement('style');
  style.textContent =
    '#cookie-banner{position:fixed;bottom:0;left:0;right:0;background:#1a1a2e;color:#fff;padding:1rem 1.5rem;z-index:9999;box-shadow:0 -2px 12px rgba(0,0,0,.3);}' +
    '.cookie-content{max-width:900px;margin:0 auto;display:flex;align-items:center;gap:1.5rem;flex-wrap:wrap;}' +
    '.cookie-content p{margin:0;font-size:.9rem;line-height:1.5;flex:1;min-width:200px;}' +
    '.cookie-content a{color:#f0c040;text-decoration:underline;}' +
    '.cookie-actions{display:flex;gap:.75rem;flex-shrink:0;}' +
    '.cookie-btn-accept{background:#f0c040;color:#1a1a2e;border:none;padding:.5rem 1.25rem;border-radius:6px;cursor:pointer;font-weight:700;font-size:.9rem;}' +
    '.cookie-btn-reject{background:transparent;color:#ccc;border:1px solid #555;padding:.5rem 1.25rem;border-radius:6px;cursor:pointer;font-size:.9rem;}' +
    '.cookie-btn-accept:hover{background:#e0b030;}' +
    '.cookie-btn-reject:hover{color:#fff;border-color:#aaa;}';

  document.head.appendChild(style);
  document.body.appendChild(banner);

  document.getElementById('cookie-accept').addEventListener('click', function () {
    localStorage.setItem('cookie_consent', 'all');
    banner.remove();
  });

  document.getElementById('cookie-reject').addEventListener('click', function () {
    localStorage.setItem('cookie_consent', 'necessary');
    banner.remove();
  });
})();
