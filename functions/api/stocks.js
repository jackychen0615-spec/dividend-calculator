/**
 * Cloudflare Pages Function — /api/stocks
 *
 * 合併 TWSE 兩個 API：
 * 1. BWIBBU_ALL — 殖利率、本益比
 * 2. STOCK_DAY_ALL — 收盤價、成交量
 *
 * 快取 1 小時，避免每次都打 TWSE
 */

export async function onRequest(context) {
  const cache = caches.default;
  const cacheKey = new Request('https://gulicalc.com/api/stocks', context.request);

  // 先查快取
  let cached = await cache.match(cacheKey);
  if (cached) {
    return cached;
  }

  try {
    // 同時打兩個 API
    const [yieldRes, priceRes] = await Promise.all([
      fetch('https://openapi.twse.com.tw/v1/exchangeReport/BWIBBU_ALL', {
        headers: { 'Accept': 'application/json' }
      }),
      fetch('https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL', {
        headers: { 'Accept': 'application/json' }
      })
    ]);

    if (!yieldRes.ok || !priceRes.ok) {
      return new Response(JSON.stringify({ error: 'TWSE API error' }), {
        status: 502,
        headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' }
      });
    }

    const yieldData = await yieldRes.json();
    const priceData = await priceRes.json();

    // 建立收盤價 map
    const priceMap = {};
    for (const item of priceData) {
      if (item.Code && item.ClosingPrice) {
        priceMap[item.Code] = {
          price: parseFloat(item.ClosingPrice) || 0,
          volume: parseInt(item.TradeVolume) || 0,
          change: parseFloat(item.Change) || 0
        };
      }
    }

    // 合併資料
    const stocks = [];
    for (const item of yieldData) {
      if (!item.Code || !item.Name) continue;

      const priceInfo = priceMap[item.Code] || {};
      const dividendYield = parseFloat(item.DividendYield) || 0;
      const price = priceInfo.price || 0;

      // 從殖利率反算每股股利：dividend = price * yield / 100
      const dividend = price > 0 && dividendYield > 0
        ? Math.round(price * dividendYield / 100 * 100) / 100
        : 0;

      stocks.push({
        code: item.Code,
        name: item.Name.trim(),
        price: price,
        dividendYield: dividendYield,
        dividend: dividend,
        pe: parseFloat(item.PEratio) || null,
        pb: parseFloat(item.PBratio) || null,
        volume: priceInfo.volume || 0,
        change: priceInfo.change || 0
      });
    }

    // 加入 ETF 即時價：BWIBBU 殖利率資料不含 ETF，但 STOCK_DAY_ALL 有即時收盤價。
    // ETF 配息資料 TWSE 不提供，留 null，由前端的 stocks.json 補配息、用此即時價算殖利率。
    const added = new Set(stocks.map(s => s.code));
    for (const item of priceData) {
      const code = item.Code;
      if (!code || added.has(code)) continue;
      if (!/^00\d{3,4}$/.test(code)) continue; // ETF 代號 00 開頭
      const price = parseFloat(item.ClosingPrice) || 0;
      if (price <= 0) continue;
      stocks.push({
        code: code,
        name: (item.Name || '').trim(),
        price: price,
        dividendYield: null,
        dividend: null,
        pe: null,
        pb: null,
        volume: parseInt(item.TradeVolume) || 0,
        change: parseFloat(item.Change) || 0
      });
    }

    const result = {
      lastUpdated: new Date().toISOString().slice(0, 10),
      count: stocks.length,
      stocks: stocks
    };

    const response = new Response(JSON.stringify(result), {
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Cache-Control': 'public, max-age=3600' // 1 小時
      }
    });

    // 存入快取
    context.waitUntil(cache.put(cacheKey, response.clone()));

    return response;

  } catch (err) {
    return new Response(JSON.stringify({ error: err.message }), {
      status: 500,
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' }
    });
  }
}
