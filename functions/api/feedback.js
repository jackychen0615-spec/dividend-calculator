/**
 * 使用者回饋 → Telegram 通知站長。
 * 前端 feedback.js 以 sendBeacon POST { rating, page, message }（text/plain）。
 * 需在 Cloudflare Pages（Production）環境變數設定：TG_BOT_TOKEN、TG_CHAT_ID。
 * 加 ?debug=1 可回傳診斷（不外洩金鑰本身）。
 */
export async function onRequestPost({ request, env }) {
  const debug = new URL(request.url).searchParams.get("debug") === "1";

  let data = {};
  try {
    data = JSON.parse(await request.text());
  } catch (e) {
    data = {};
  }

  const r = Math.max(0, Math.min(5, parseInt(data.rating, 10) || 0));
  const stars = "★".repeat(r) + "☆".repeat(5 - r);
  const page = String(data.page || "").slice(0, 200);
  const message = String(data.message || "(無留言)").slice(0, 1000);

  const token = env.TG_BOT_TOKEN;
  const chat = env.TG_CHAT_ID;

  let tgStatus = "skipped-no-env";
  let tgBody = "";
  if (token && chat) {
    const text =
      "💬 gulicalc 有新回饋\n\n" +
      "評分：" + stars + "（" + r + "/5）\n" +
      "頁面：" + page + "\n" +
      "留言：" + message;
    try {
      const resp = await fetch("https://api.telegram.org/bot" + token + "/sendMessage", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chat_id: chat, text: text, disable_web_page_preview: true }),
      });
      tgStatus = "http-" + resp.status;
      tgBody = (await resp.text()).slice(0, 300);
    } catch (e) {
      tgStatus = "fetch-error";
      tgBody = String(e).slice(0, 200);
    }
  }

  const out = { ok: true };
  if (debug) {
    out.debug = {
      hasToken: !!token,
      tokenLen: token ? token.length : 0,
      hasChat: !!chat,
      chatValue: chat || null,
      tgStatus: tgStatus,
      tgBody: tgBody,
    };
  }

  return new Response(JSON.stringify(out), {
    headers: { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
  });
}

// build bump 1783093882
