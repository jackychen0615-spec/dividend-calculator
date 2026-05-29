/* 深色模式：全站共用。自動插入切換鈕、跨頁記憶、SVG 圖示 */
(function () {
  var html = document.documentElement;
  var MOON = '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>';
  var SUN = '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>';

  function isDark() { return html.getAttribute('data-theme') === 'dark'; }
  function apply(dark) { if (dark) html.setAttribute('data-theme', 'dark'); else html.removeAttribute('data-theme'); }

  function init() {
    var btn = document.getElementById('themeToggle');
    if (!btn) {
      var nav = document.querySelector('.nav-container') || document.querySelector('header nav') || document.querySelector('.nav-bar');
      if (nav) {
        btn = document.createElement('button');
        btn.id = 'themeToggle';
        btn.className = 'theme-toggle';
        btn.type = 'button';
        btn.setAttribute('aria-label', '切換深色模式');
        btn.title = '切換深色模式';
        nav.appendChild(btn);
      }
    }
    apply(localStorage.getItem('gulicalc_theme') === 'dark');
    if (!btn) return;
    btn.innerHTML = isDark() ? SUN : MOON;
    btn.addEventListener('click', function () {
      apply(!isDark());
      btn.innerHTML = isDark() ? SUN : MOON;
      try { localStorage.setItem('gulicalc_theme', isDark() ? 'dark' : 'light'); } catch (e) {}
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
