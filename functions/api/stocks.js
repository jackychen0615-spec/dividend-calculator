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

  // 快取策略（Client-facing Cache-Control，維持原本邏輯不變）
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

  // Phase 5A｜Shared Market Snapshot Cache（2026-09-24 micro fix）：
  //
  // 第一版的 edge cache 曾經用「含 querystring 的完整 URL」當 cache key，
  // 結果 ?code=2330 和 ?code=2454 是兩個不同的 key——但兩者在 filter 前
  // 建的是同一份 full-market dataset，所以不同 symbol 第一次都各自 cache
  // miss、各自重打一輪 2~4 個 TWSE upstream request，沒有真正省到。
  //
  // 改成快取「未篩選的完整 market snapshot」本身，用一個代表這份 snapshot
  // 的**固定** internal key（market-snapshot-v1）。這裡的「固定 key」跟
  // 上一版擔心、以及更早 etf-dividends.js 那次事故的「固定 key」不是同一
  // 回事：那次事故是把**不同 query 的最終 response** 混進同一個 key，
  // 導致 A 的回應被 B 拿去用。這裡固定 key 代表的是「未篩選、對所有 query
  // 都一樣」的原始資料，篩選永遠是在拿到 snapshot（不管來自 cache 還是剛
  // 抓好）之後才做，每個 request 都用自己的 ?code= 篩出自己要的東西，不會
  // 把 A 的回應直接送給 B。
  //
  // TTL 一樣是 120 秒（60~300 秒區間內），短到部署後最多 2 分鐘內就會自然
  // 過期。Upstream 發生錯誤時不快取（見下方 try/catch，只有成功組好
  // stocks 之後才會呼叫 cache.put）。
  const EDGE_CACHE_TTL = 120;
  const cache = caches.default;
  const snapshotCacheKey = new Request('https://gulicalc-internal.invalid/api/stocks/market-snapshot-v1');

  let stocks = null;
  let cacheStatus = 'MISS';

  const cachedSnapshot = await cache.match(snapshotCacheKey);
  if (cachedSnapshot) {
    try {
      const cachedJson = await cachedSnapshot.json();
      if (Array.isArray(cachedJson.stocks)) {
        stocks = cachedJson.stocks;
        cacheStatus = 'HIT';
      }
    } catch (e) {
      stocks = null; // 快取內容壞掉：當作沒快取，往下重新抓
    }
  }

  if (stocks === null) {
    try {
      stocks = [];
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
          // upstream 失敗：不快取，直接回錯誤
          return new Response(JSON.stringify({ error: 'TWSE API error' }), {
            status: 502,
            headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*', 'X-GULICALC-CACHE': 'MISS' }
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
          if (!/^00\d{2,4}L?$/.test(code)) continue;
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

      // 只有成功組好完整 snapshot 才快取（不快取 upstream 錯誤/空結果）。
      if (stocks.length > 0) {
        context.waitUntil(cache.put(snapshotCacheKey, new Response(JSON.stringify({ stocks }), {
          headers: {
            'Content-Type': 'application/json',
            'Cache-Control': `public, max-age=${EDGE_CACHE_TTL}`
          }
        })));
      }

    } catch (err) {
      // upstream 拋錯：不快取，直接回錯誤
      return new Response(JSON.stringify({ error: err.message }), {
        status: 500,
        headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*', 'X-GULICALC-CACHE': 'MISS' }
      });
    }
  }

  // Phase 5A — 選用的 symbol-scoped query：/api/stocks?code=2330 只回單一
  // 標的，給 42 個 article page 的 live-price-layer 用，避免每頁都下載
  // 整包 ~1200+ 檔（gzip 後約 39KB）。不管 stocks 是剛抓的還是從 shared
  // snapshot cache 來的，篩選永遠在這裡對「這次 request 自己的 ?code=」
  // 做，不會把別的 request 篩好的結果重複使用。無 code 時行為與之前完全
  // 一樣（回完整 stocks[]），backward-compatible，不影響首頁 search。
  const url = new URL(context.request.url);
  const codeParam = url.searchParams.get('code');
  const responseStocks = codeParam
    ? stocks.filter((s) => s.code === codeParam)
    : stocks;

  const result = {
    lastUpdated: new Date().toISOString(),
    mode: isMarketHours ? 'realtime' : 'closing',
    cacheTTL: cacheTTL,
    count: responseStocks.length,
    stocks: responseStocks
  };

  // Client-facing Cache-Control 維持原本的 cacheTTL（不改變既有語意）。
  // X-GULICALC-CACHE 標示這次的 stocks 資料是從 shared snapshot cache
  // 命中（HIT，0 upstream call）還是這次現抓的（MISS）——方便驗證，
  // 不影響任何既有邏輯，cf-cache-status 本身不足以反映 caches.default
  // 的命中狀態。
  return new Response(JSON.stringify(result), {
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      'Cache-Control': `public, max-age=${cacheTTL}`,
      'X-GULICALC-CACHE': cacheStatus
    }
  });
}
