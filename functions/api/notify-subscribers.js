/**
 * Cloudflare Pages Function — /api/notify-subscribers
 *
 * POST: 寄「新文章上架」通知給所有 active 訂閱者（透過 Resend）
 *
 * Body(JSON): { key, title, url, summary }
 *   key     = 管理密鑰（對應環境變數 NOTIFY_ADMIN_KEY）
 *   title   = 文章標題
 *   url     = 文章網址（完整 https://...）
 *   summary = 文章摘要（選填）
 *
 * 需要的環境變數（在 Cloudflare Pages → 設定 → 環境變數/密鑰 設定）:
 *   RESEND_API_KEY   = Resend 的 API key（密鑰）
 *   NOTIFY_ADMIN_KEY = 你自訂的管理密鑰（密鑰）
 * 需要的繫結:
 *   DB = D1 資料庫 gulicalc-seo-db（newsletter 已在用，沿用即可）
 */

export async function onRequest(context) {
  const { request, env } = context;
  const cors = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  };
  const json = (obj, status = 200) =>
    new Response(JSON.stringify(obj), { status, headers: { 'Content-Type': 'application/json', ...cors } });

  if (request.method === 'OPTIONS') return new Response(null, { headers: cors });
  if (request.method !== 'POST') return json({ error: 'Method not allowed' }, 405);

  let body;
  try { body = await request.json(); } catch (e) { return json({ error: '無效的 JSON' }, 400); }

  const adminKey = env.NOTIFY_ADMIN_KEY;
  if (!adminKey) return json({ error: '伺服器未設定 NOTIFY_ADMIN_KEY' }, 500);
  if (body.key !== adminKey) return json({ error: '需要授權' }, 401);

  const { title, url, summary } = body;
  if (!title || !url) return json({ error: '缺少 title 或 url' }, 400);

  const db = env.DB;
  if (!db) return json({ error: 'Database not available' }, 500);
  const RESEND = env.RESEND_API_KEY;
  if (!RESEND) return json({ error: '伺服器未設定 RESEND_API_KEY' }, 500);

  // 撈出所有 active 訂閱者
  const rows = await db.prepare("SELECT email FROM newsletter WHERE status = 'active'").all();
  const emails = (rows.results || []).map((r) => r.email).filter(Boolean);
  if (!emails.length) return json({ ok: true, sent: 0, message: '目前沒有 active 訂閱者' });

  const SITE = 'https://gulicalc.com';
  const FROM = 'GULICALC 股利計算器 <news@gulicalc.com>'; // ← 需是已驗證的寄件網域
  const safeSummary = (summary || '').toString().slice(0, 300);

  const buildHtml = (email) => {
    const unsub = `${SITE}/api/newsletter?unsubscribe=${encodeURIComponent(email)}`;
    return `<!DOCTYPE html><html lang="zh-TW"><body style="margin:0;background:#f4f6f5;font-family:-apple-system,'PingFang TC','Microsoft JhengHei',sans-serif;">
  <div style="max-width:520px;margin:0 auto;padding:24px 16px;">
    <div style="background:#fff;border-radius:14px;overflow:hidden;border:1px solid #e5e7eb;">
      <div style="background:#0d8c84;padding:16px 20px;color:#fff;font-weight:700;font-size:15px;">GULICALC 股利計算器 · 新文章上架</div>
      <div style="padding:22px 20px;">
        <h1 style="margin:0 0 10px;font-size:19px;line-height:1.4;color:#14201f;">${title}</h1>
        ${safeSummary ? `<p style="margin:0 0 18px;font-size:14px;line-height:1.7;color:#46555a;">${safeSummary}</p>` : ''}
        <a href="${url}" style="display:inline-block;background:#0d8c84;color:#fff;text-decoration:none;font-weight:600;font-size:14px;padding:11px 22px;border-radius:9px;">閱讀全文 →</a>
      </div>
    </div>
    <p style="text-align:center;font-size:12px;color:#9aa6a4;margin:18px 0 0;line-height:1.6;">
      你收到這封信是因為訂閱了 GULICALC 電子報。<br>
      <a href="${unsub}" style="color:#0d8c84;">取消訂閱</a>
    </p>
  </div>
</body></html>`;
  };

  // Resend 批次寄送（每批最多 100 封；每封各自 to 單一收件人，不互相曝光）
  let sent = 0;
  const errors = [];
  for (let i = 0; i < emails.length; i += 100) {
    const chunk = emails.slice(i, i + 100);
    const batch = chunk.map((e) => ({
      from: FROM,
      to: e,
      subject: `📈 新文章：${title}`,
      html: buildHtml(e),
      headers: { 'List-Unsubscribe': `<${SITE}/api/newsletter?unsubscribe=${encodeURIComponent(e)}>` },
    }));
    try {
      const res = await fetch('https://api.resend.com/emails/batch', {
        method: 'POST',
        headers: { Authorization: `Bearer ${RESEND}`, 'Content-Type': 'application/json' },
        body: JSON.stringify(batch),
      });
      if (res.ok) sent += chunk.length;
      else errors.push(`HTTP ${res.status}: ${(await res.text()).slice(0, 200)}`);
    } catch (err) {
      errors.push(err.message);
    }
  }

  return json({ ok: errors.length === 0, sent, total: emails.length, errors });
}
