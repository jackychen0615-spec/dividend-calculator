/**
 * Cloudflare Pages Function — /api/newsletter
 *
 * POST: 訂閱（存 email 到 D1）
 * GET:  查看訂閱者名單（需要 admin key）
 */

export async function onRequest(context) {
  const { request, env } = context;
  // D1 binding 名稱：在 Cloudflare Pages Dashboard 設定
  // Pages → 設定 → 函式 → D1 資料庫繫結 → 變數名稱: DB → 選 gulicalc-seo-db
  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  };

  if (request.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders });
  }

  // POST: 訂閱
  if (request.method === 'POST') {
    try {
      const { email } = await request.json();

      if (!email || !email.includes('@')) {
        return new Response(JSON.stringify({ error: '請輸入有效的 email' }), {
          status: 400,
          headers: { 'Content-Type': 'application/json', ...corsHeaders }
        });
      }

      const db = env.DB;
      if (!db) {
        return new Response(JSON.stringify({ error: 'Database not available' }), {
          status: 500,
          headers: { 'Content-Type': 'application/json', ...corsHeaders }
        });
      }

      // 檢查是否已訂閱
      const existing = await db.prepare('SELECT email, status FROM newsletter WHERE email = ?').bind(email.toLowerCase()).first();

      if (existing) {
        if (existing.status === 'active') {
          return new Response(JSON.stringify({ ok: true, message: '你已經訂閱過了！' }), {
            headers: { 'Content-Type': 'application/json', ...corsHeaders }
          });
        }
        // 重新啟用
        await db.prepare('UPDATE newsletter SET status = ?, subscribed_at = datetime(?) WHERE email = ?')
          .bind('active', 'now', email.toLowerCase()).run();
        return new Response(JSON.stringify({ ok: true, message: '歡迎回來！已重新訂閱。' }), {
          headers: { 'Content-Type': 'application/json', ...corsHeaders }
        });
      }

      // 新訂閱
      await db.prepare('INSERT INTO newsletter (email) VALUES (?)').bind(email.toLowerCase()).run();

      return new Response(JSON.stringify({ ok: true, message: '訂閱成功！每週會收到存股精選。' }), {
        headers: { 'Content-Type': 'application/json', ...corsHeaders }
      });

    } catch (err) {
      return new Response(JSON.stringify({ error: err.message }), {
        status: 500,
        headers: { 'Content-Type': 'application/json', ...corsHeaders }
      });
    }
  }

  // GET: 查看名單（需要 admin key）
  if (request.method === 'GET') {
    const url = new URL(request.url);
    const key = url.searchParams.get('key');

    // 簡單的 admin 驗證（你可以改成更安全的）
    if (key !== 'gulicalc2026admin') {
      return new Response(JSON.stringify({ error: '需要授權' }), {
        status: 401,
        headers: { 'Content-Type': 'application/json', ...corsHeaders }
      });
    }

    const db = env.DB;
    if (!db) {
      return new Response(JSON.stringify({ error: 'Database not available' }), {
        status: 500,
        headers: { 'Content-Type': 'application/json', ...corsHeaders }
      });
    }

    const results = await db.prepare('SELECT email, subscribed_at, status FROM newsletter ORDER BY subscribed_at DESC').all();
    const total = await db.prepare('SELECT COUNT(*) as count FROM newsletter WHERE status = ?').bind('active').first();

    return new Response(JSON.stringify({
      total: total?.count || 0,
      subscribers: results.results || []
    }), {
      headers: { 'Content-Type': 'application/json', ...corsHeaders }
    });
  }

  return new Response('Method not allowed', { status: 405 });
}
