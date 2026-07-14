/**
 * Cloudflare Pages Function — /api/stocks
 *
 * 盤中（週一到五 9:00-14:00 台灣時間）：
 *   用 mis.twse.com.tw 即時報價 + BWIBBU 殖利率，快取 5 分鐘
 * 盤後 / 週末：
 *   用 STOCK_DAY_ALL 收盤價 + BWIBBU 殖利率，快取 1-6 小時
 */

export async function onRequest(context) {
  // 判斷台灣時間
  const now = new Date();
  const twHour = (now.getUTCHours() + 8) % 24;
  const twDay = new Date(now.getTime() + 8 * 3600 * 1000).getUTCDay(); // 0=Sun, 6=Sat
  const isWeekday = twDay >= 1 && twDay <= 5;
  const isMarketHours = isWeekday && twHour >= 9 && twHour < 14;
  const isAfterClose = isWeekday && twHour >= 14 && twHour < 15;

  // 快取策略
  let cacheTTL;
  if (isMarketHours) {
    cacheTTL = 300; // 盤中：5 分鐘
  } else if (isAfterClose) {
    cacheTTL = 3600; // 剛收盤：1 小時
  } else if (!isWeekday) {
    cacheTTL = 21600; // 週末：6 小時
  } else {
    cacheTTL = 3600; // 盤前/盤後：1 小時
  }

  const cacheVersion = isMarketHours ? 'realtime' : 'close';
  const cache = caches.default;
  const cacheKey = new Request(`https://gulicalc.com/api/stocks?v=3&m=${cacheVersion}`, context.request);

  // 先查快取
  let cached = await cache.match(cacheKey);
  if (cached) {
    return cached;
  }

  try {
    let stocks = [];
    const headers = { 'Accept': 'application/json', 'User-Agent': 'GULICALC/1.0' };

    // 永遠抓殖利率資料
    let yieldMap = {};
    try {
      const yieldRes = await fetch('https://openapi.twse.com.tw/v1/exchangeReport/BWIBBU_ALL', { headers });
      if (yieldRes.ok) {
        const yieldData = await yieldRes.json();
        for (const item of yieldData) {
          if (item.Code) {
            yieldMap[item.Code] = {
              dividendYield: parseFloat(item.DividendYield) || 0,
              pe: parseFloat(item.PEratio) || null,
              pb: parseFloat(item.PBratio) || null
            };
          }
        }
      }
    } catch (e) { /* continue without yield data */ }

    if (isMarketHours) {
      // === 盤中：用即時報價 API ===
      // mis.twse.com.tw 一次最多查 20 檔，我們查熱門標的
      const hotCodes = [
        '0050','0056','00713','00878','00919','00929','00940','006208',
        '00882','00900','00915','00918','00927','00932','00934','00936','00939','00943',
        '2330','2317','2382','2454',
        '2881','2882','2884','2886','2891','2892','5880',
        '1216','1301','2412','2603','2308','2883','2880'
      ];

      // 分批查（每批 20 檔）
      const batches = [];
      for (let i = 0; i < hotCodes.length; i += 20) {
        batches.push(hotCodes.slice(i, i + 20));
      }

      for (const batch of batches) {
        const exCh = batch.map(c => `tse_${c}.tw`).join('|');
        try {
          const rtRes = await fetch(`https://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch=${exCh}`, { headers });
          if (rtRes.ok) {
            const rtData = await rtRes.json();
            if (rtData.msgArray) {
              for (const item of rtData.msgArray) {
                const code = item.c;
                const price = parseFloat(item.z) || parseFloat(item.y) || 0; // z=成交價, y=昨收
                const prevClose = parseFloat(item.y) || 0;
                const change = price > 0 && prevClose > 0 ? Math.round((price - prevClose) * 100) / 100 : 0;
                const changePercent = prevClose > 0 ? Math.round((change / prevClose * 100) * 100) / 100 : 0;
                const volume = parseInt(item.v) || 0;

                const yi = yieldMap[code] || {};
                const dividendYield = yi.dividendYield || 0;
                const dividend = price > 0 && dividendYield > 0
                  ? Math.round(price * dividendYield / 100 * 100) / 100 : 0;

                stocks.push({
                  code: code,
                  name: (item.n || '').trim(),
                  price: price,
                  dividendYield: dividendYield || null,
                  dividend: dividend || null,
                  pe: yi.pe || null,
                  pb: yi.pb || null,
                  volume: volume,
                  change: change,
                  changePercent: changePercent,
                  realtime: true
                });
              }
            }
          }
        } catch (e) { /* skip batch */ }
      }

      // 補充：抓 STOCK_DAY_ALL 填補即時 API 沒有的股票
      try {
        const priceRes = await fetch('https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL', { headers });
        if (priceRes.ok) {
          const priceData = await priceRes.json();
          const existCodes = new Set(stocks.map(s => s.code));
          for (const item of priceData) {
            if (!item.Code || existCodes.has(item.Code)) continue;
            const price = parseFloat(item.ClosingPrice) || 0;
            if (price <= 0) continue;
            const yi = yieldMap[item.Code] || {};
            const dividendYield = yi.dividendYield || 0;
            const dividend = price > 0 && dividendYield > 0
              ? Math.round(price * dividendYield / 100 * 100) / 100 : 0;
            // TWSE 的 Change 是「絕對點數」不是百分比；換算成真正的漲跌幅 %
            const change = parseFloat(item.Change) || 0;
            const prevClose = price - change;
            const changePercent = prevClose > 0 ? Math.round((change / prevClose * 100) * 100) / 100 : 0;

            stocks.push({
              code: item.Code,
              name: (item.Name || '').trim(),
              price: price,
              dividendYield: dividendYield || null,
              dividend: dividend || null,
              pe: yi.pe || null,
              pb: yi.pb || null,
              volume: parseInt(item.TradeVolume) || 0,
              change: change,
              changePercent: changePercent,
              realtime: false
            });
          }
        }
      } catch (e) { /* continue */ }

    } else {
      // === 盤後 / 週末：用收盤價 API ===
      const priceRes = await fetch('https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL', { headers });
      if (!priceRes.ok) {
        return new Response(JSON.stringify({ error: 'TWSE API error' }), {
          status: 502,
          headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' }
        });
      }

      const priceData = await priceRes.json();
      const priceMap = {};
      for (const item of priceData) {
        if (item.Code && item.ClosingPrice) {
          // TWSE 的 Change 是「絕對點數」不是百分比；換算成真正的漲跌幅 %
          const pPrice = parseFloat(item.ClosingPrice) || 0;
          const pChange = parseFloat(item.Change) || 0;
          const pPrevClose = pPrice - pChange;
          priceMap[item.Code] = {
            name: (item.Name || '').trim(),
            price: pPrice,
            volume: parseInt(item.TradeVolume) || 0,
            change: pChange,
            changePercent: pPrevClose > 0 ? Math.round((pChange / pPrevClose * 100) * 100) / 100 : 0
          };
        }
      }

      // 合併殖利率 + 收盤價
      const addedCodes = new Set();
      for (const code in yieldMap) {
        const yi = yieldMap[code];
        const pi = priceMap[code] || {};
        const price = pi.price || 0;
        const dividendYield = yi.dividendYield || 0;
        const dividend = price > 0 && dividendYield > 0
          ? Math.round(price * dividendYield / 100 * 100) / 100 : 0;

        stocks.push({
          code: code,
          name: pi.name || code,
          price: price,
          dividendYield: dividendYield,
          dividend: dividend,
          pe: yi.pe,
          pb: yi.pb,
          volume: pi.volume || 0,
          change: pi.change || 0,
          changePercent: pi.changePercent || 0,
          realtime: false
        });
        addedCodes.add(code);
      }

      // 補 ETF（BWIBBU 不含 ETF）
      for (const item of priceData) {
        const code = item.Code;
        if (!code || addedCodes.has(code)) continue;
        if (!/^00\d{2,4}$/.test(code)) continue;
        const price = parseFloat(item.ClosingPrice) || 0;
        if (price <= 0) continue;
        // TWSE 的 Change 是「絕對點數」不是百分比；換算成真正的漲跌幅 %
        const etfChange = parseFloat(item.Change) || 0;
        const etfPrevClose = price - etfChange;
        stocks.push({
          code: code,
          name: (item.Name || '').trim(),
          price: price,
          dividendYield: null,
          dividend: null,
          pe: null,
          pb: null,
          volume: parseInt(item.TradeVolume) || 0,
          change: etfChange,
          changePercent: etfPrevClose > 0 ? Math.round((etfChange / etfPrevClose * 100) * 100) / 100 : 0,
          realtime: false
        });
      }
    }

    const result = {
      lastUpdated: new Date().toISOString(),
      mode: isMarketHours ? 'realtime' : 'closing',
      cacheTTL: cacheTTL,
      count: stocks.length,
      stocks: stocks
    };

    const response = new Response(JSON.stringify(result), {
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Cache-Control': `public, max-age=${cacheTTL}`
      }
    });

    context.waitUntil(cache.put(cacheKey, response.clone()));
    return response;

  } catch (err) {
    return new Response(JSON.stringify({ error: err.message }), {
      status: 500,
      headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' }
    });
  }
}
