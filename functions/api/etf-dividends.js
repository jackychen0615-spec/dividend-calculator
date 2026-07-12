/**
 * ETF 即時配息/殖利率 API（Cloudflare Pages Function）
 * - 股價：即時抓 TWSE 官方 STOCK_DAY_ALL（收盤價），邊緣快取 6 小時。
 * - 配息：用下方設定檔（ETF 年配息一年只變幾次，由成長引擎維護；
 *   驗證來源 TWSE STOCK_DAY_ALL 官方價 + 財報狗/各投信公告）。
 * - 殖利率 = 年配息 ÷ 現價，永遠用現價算，不會像寫死的頁面過期。
 * 回傳：{ updated, source, data:{ "0056":{name,price,dividend,freq,yield}, ... } }
 * 用途：ETF 頁前端呼叫 /api/etf-dividends 即時更新計算器與殖利率。
 */

// 年度配息設定（元/受益權單位）。新配息公告時更新此表即可。
const ETF_DIV = {
  "0050":   { name: "元大台灣50",       dividend: 3.0,  freq: "季配" },
  "0056":   { name: "元大高股息",       dividend: 3.87, freq: "季配" },
  "00878":  { name: "國泰永續高股息",   dividend: 1.77, freq: "季配" },
  "00713":  { name: "元大台灣高息低波", dividend: 4.68, freq: "季配" },
  "00929":  { name: "復華台灣科技優息", dividend: 1.63, freq: "月配" },
  "00939":  { name: "統一台灣高息動能", dividend: 0.9,  freq: "季配" },
  "00940":  { name: "元大台灣價值高息", dividend: 0.43, freq: "月配" },
  "00918":  { name: "大華優利高填息30", dividend: 2.48, freq: "季配" },
  "006208": { name: "富邦台50",         dividend: 3.5,  freq: "年配" },
};

const TWSE_URL = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL";
const TTL = 21600; // 6 小時

export async function onRequest() {
  // 不用 caches.default 手動快取（跨部署不會清、會卡住舊配息）。
  // 改為：TWSE 股價用 cf.cacheTtl 邊緣快取 6h（不狂打上游），我們的回應每次現算，
  // 配息設定一改（部署後）立即生效；回應本身用 Cache-Control 讓 CDN 短快取 30 分。
  let prices = {};
  try {
    const rows = await fetch(TWSE_URL, { cf: { cacheTtl: TTL, cacheEverything: true } }).then((r) => r.json());
    for (const r of rows) {
      const c = r.Code;
      if (ETF_DIV[c]) {
        const p = parseFloat(r.ClosingPrice);
        if (p > 0) prices[c] = p;
      }
    }
  } catch (e) {
    // TWSE 抓失敗：回傳只有設定檔的配息、股價/殖利率留 null（前端自行處理）
  }

  const data = {};
  for (const [code, info] of Object.entries(ETF_DIV)) {
    const price = prices[code] ?? null;
    const y = price ? Math.round((info.dividend / price) * 1000) / 10 : null; // 一位小數
    data[code] = { name: info.name, price, dividend: info.dividend, freq: info.freq, yield: y };
  }

  const body = JSON.stringify({
    updated: new Date().toISOString(),
    source: "TWSE STOCK_DAY_ALL（收盤價）+ 站內配息設定",
    data,
  });

  return new Response(body, {
    headers: {
      "content-type": "application/json; charset=utf-8",
      "cache-control": "public, max-age=1800",
      "access-control-allow-origin": "*",
    },
  });
}
